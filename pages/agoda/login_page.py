from __future__ import annotations
import allure
from core.element.conditions import Condition
from core.element.conditions import enabled as c
from core.element.conditions import enabled as cond_enabled
from core.element.conditions import visible as cond_visible
from core.element.locator import Locator
from core.utils.browser_utils import BrowserUtils
from pages.base_page import BasePage


class LoginPage(BasePage):
    def __init__(self):
        super().__init__()

    # -------- LOGIN FORM ---------
    _PARENT = Locator.xpath("//div[@data-cy='mutation-sensor']", "LOGIN_PAGE Login form")
    _TXT_LOGIN_USERNAME = Locator.xpath("//input[@type='email']", "LOGIN_PAGE User name field")
    _BTN_LOGIN_CONTINUE = Locator.xpath("//button[@data-element-name='universal-login-unified-auth-email-continue']"
                                        , "LOGIN_PAGE Continue button")

    @allure.step("Wait for Login form display")
    def wait_login_form_display(self) -> "Element":
        return self.el(self._PARENT).should_be(cond_visible())

    @allure.step("Fill username: {user_name}")
    def fill_email_username(self, user_name: str):
        user_name_input = self.wait_login_form_display().find(self._TXT_LOGIN_USERNAME)
        user_name_input.type(user_name)

    @allure.step("Wait for LOGIN button enable")
    def wait_login_button(self) -> "Element":
        return self.el(self._BTN_LOGIN_CONTINUE).should_be(cond_enabled())

    @allure.step("Click LOGIN button")
    def click_continue(self):
        cont_btn = self.wait_login_button()
        cont_btn.click()

    @allure.step("Login with username : {user_name}")
    def login(self, user_name: str):
        self.fill_email_username(user_name)
        self.click_continue()

