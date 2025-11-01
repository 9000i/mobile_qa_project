
import os
import subprocess
import pytest
from appium import webdriver
from appium.options.common import AppiumOptions

@pytest.fixture(scope="session")
def driver():
    """Decide where to run (local ADB or BrowserStack) and return Appium driver."""
    device_detected = False
    try:
        output = subprocess.check_output(["adb", "devices"]).decode()
        device_detected = len(output.strip().splitlines()) > 1
    except Exception:
        pass

    if device_detected:
        print("Local device detected — running via local Appium server.")
        appium_server = "http://127.0.0.1:4723/wd/hub"
        desired_caps = {
            "platformName": "Android",
            "deviceName": "emulator-5554",
            "automationName": "UiAutomator2",
            "appPackage": "org.wikipedia",
            "appActivity": ".main.MainActivity",
            "noReset": True,
        }
    else:
        print("No local device found — running on BrowserStack Cloud.")
        appium_server = f"http://{os.getenv('BROWSERSTACK_USERNAME')}:{os.getenv('BROWSERSTACK_ACCESS_KEY')}@hub.browserstack.com/wd/hub"
        
        desired_caps = {
            "platformName": "Android",
            "deviceName": "Google Pixel 7",
            "os_version": "13.0",
            "project": "Wikipedia Sample App Test",
            "build": "pytest_appium_browserstack_demo",
            "name": "test_open_search",
            "app": os.getenv("BROWSERSTACK_APP_ID"),
            "browserstack.user": os.getenv("BROWSERSTACK_USERNAME"),
            "browserstack.key": os.getenv("BROWSERSTACK_ACCESS_KEY"),
            "automationName": "UiAutomator2",
        }

    # Proper way for Selenium 4.15+ / Appium 2.x
    options = AppiumOptions()
    options.load_capabilities(desired_caps)
    driver = webdriver.Remote(appium_server, options = options)

    yield driver
    driver.quit()



@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Execute all other hooks to obtain the report object
    outcome = yield
    rep = outcome.get_result()

    # We only care about test failures during the "call" phase
    if rep.when == "call" and rep.failed:
        driver = item.funcargs.get("driver")
        if driver:
            screenshot_dir = os.path.join(os.getcwd(), "screenshots")
            os.makedirs(screenshot_dir, exist_ok=True)

            file_name = f"{item.name}.png"
            destination_file = os.path.join(screenshot_dir, file_name)
            driver.save_screenshot(destination_file)

            # Attach the screenshot to the pytest-html report
            if hasattr(rep, "extra"):
                import pytest_html
                rep.extra.append(pytest_html.extras.image(destination_file))

def download_browserstack_logs(session_id, save_dir):
    """Download Appium and device logs from BrowserStack."""
    username = os.getenv("BROWSERSTACK_USERNAME")
    access_key = os.getenv("BROWSERSTACK_ACCESS_KEY")

    log_types = {
        "appium": f"https://api.browserstack.com/app-automate/sessions/{session_id}/appiumlogs",
        "device": f"https://api.browserstack.com/app-automate/sessions/{session_id}/devicelogs",
    }

    os.makedirs(save_dir, exist_ok=True)

    for log_name, url in log_types.items():
        response = requests.get(url, auth=(username, access_key))
        if response.status_code == 200:
            file_path = os.path.join(save_dir, f"{log_name}_log.txt")
            with open(file_path, "wb") as f:
                f.write(response.content)
        else:
            print(f"Failed to fetch {log_name} log: {response.status_code} - {response.text}")

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_teardown(item):
    """After each test, download BrowserStack logs if applicable."""
    outcome = yield
    driver = item.funcargs.get("driver")
    if not driver:
        return

    try:
        session_id = driver.session_id
        logs_dir = os.path.join(os.getcwd(), "logs")
        download_browserstack_logs(session_id, logs_dir)

        # Optionally attach logs to pytest-html report
        report = getattr(item, "rep_call", None)
        if report and hasattr(report, "extra"):
            import pytest_html
            for log_file in os.listdir(logs_dir):
                file_path = os.path.join(logs_dir, log_file)
                report.extra.append(pytest_html.extras.text(open(file_path).read(), log_file))

    except Exception as e:
        print(f"Error during log retrieval: {e}")
