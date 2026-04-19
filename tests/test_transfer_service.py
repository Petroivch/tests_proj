from urllib.parse import urlencode

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


TRANSFER_BUTTON_TEXT = "\u041f\u0435\u0440\u0435\u0432\u0435\u0441\u0442\u0438"


def open_page(driver, app_url, *, balance, reserved):
    query = urlencode({"balance": balance, "reserved": reserved})
    driver.get(f"{app_url}?{query}")


def select_rub_account(driver):
    rub_balance = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "rub-sum"))
    )
    rub_balance.click()


def fill_card_number(driver, digits):
    card_input = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='0000 0000 0000 0000']"))
    )
    card_input.click()
    card_input.send_keys(digits)
    return card_input


def fill_amount(driver, value):
    amount_input = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='1000']"))
    )
    amount_input.send_keys(Keys.CONTROL, "a")
    amount_input.send_keys(Keys.DELETE)
    amount_input.send_keys(value)
    return amount_input


def find_transfer_button(driver):
    try:
        return driver.find_element(By.XPATH, f"//button[normalize-space()='{TRANSFER_BUTTON_TEXT}']")
    except NoSuchElementException:
        return None


def is_transfer_button_visible(driver):
    try:
        WebDriverWait(driver, 2).until(lambda current_driver: find_transfer_button(current_driver))
        return find_transfer_button(driver).is_displayed()
    except TimeoutException:
        return False


def is_amount_input_visible(driver):
    try:
        WebDriverWait(driver, 1.5).until(
            EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='1000']"))
        )
        return True
    except TimeoutException:
        return False


def test_valid_transfer_form_is_available_for_sufficient_balance(driver, app_url):
    open_page(driver, app_url, balance=5000, reserved=0)
    select_rub_account(driver)
    fill_card_number(driver, "4111111111111111")

    commission = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.ID, "comission"))
    ).text

    assert is_transfer_button_visible(driver)
    assert commission == "100"


def test_negative_amount_must_be_rejected(driver, app_url):
    open_page(driver, app_url, balance=5000, reserved=0)
    select_rub_account(driver)
    fill_card_number(driver, "4111111111111111")
    fill_amount(driver, "-1000")

    assert not is_transfer_button_visible(driver), "Negative transfer amount must not be accepted"


def test_card_number_must_not_accept_more_than_16_digits(driver, app_url):
    open_page(driver, app_url, balance=5000, reserved=0)
    select_rub_account(driver)
    fill_card_number(driver, "41111111111111112")

    assert not is_amount_input_visible(driver), "Card numbers longer than 16 digits must be rejected"
