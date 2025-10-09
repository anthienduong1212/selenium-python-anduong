import pytest
from core.drivers.driver_manager import DriverManager


@pytest.mark.parametrize("url,title", [
    ("data:text/html,<title>Welcome</title>", "Welcome"),
    ("data:text/html,<title>Demo</title>", "Demo"),
])
def test_open_page_and_title(driver, url, title):
    driver.get(url)
    assert title in driver.title


def test_driver_is_alive_and_reusable(driver):
    driver.get("https://www.agoda.com")
    session_before = driver.session_id
    # gọi lại fixture driver → framework của bạn phải tái sử dụng trong cùng ngữ cảnh
    driver.get("https://www.agoda.com")
    assert driver.session_id == session_before


def test_driver_quit_via_manager_cleans_up():
    d1 = DriverManager.get_driver()
    DriverManager.quit_driver()
    # tạo lại driver mới sau khi quit
    d2 = DriverManager.get_driver()
    assert d1.session_id != d2.session_id
