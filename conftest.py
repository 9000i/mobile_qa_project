
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
