
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_open_search(driver):
    wait = WebDriverWait(driver, 25)

    # Wait for the search bar using the ID you found
    search_bar = wait.until(
            EC.presence_of_element_located(
                (By.ID, "org.wikipedia.alpha:id/search_container")
            )
        )

    search_bar.click()

    # Once inside search, locate the input box (still valid for most Wikipedia APKs)
    search_input = wait.until(
        EC.presence_of_element_located((By.ID, "org.wikipedia.alpha:id/search_src_text"))
    )
    search_input.send_keys("Appium")

    # Wait for one result to appear and verify it
    first_result = wait.until(
        EC.presence_of_element_located((By.ID, "org.wikipedia.alpha:id/page_list_item_title"))
    )

    assert first_result.is_displayed(), "Search results not shown"
    print("Search test passed.")
