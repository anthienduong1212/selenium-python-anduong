from core.element.conditions import Condition
from core.element.conditions import enabled as c
from core.element.conditions import enabled as cond_enabled
from core.element.conditions import visible as cond_visible
from core.element.locators import Locator
from core.utils.browser_utils import BrowserUtils
from pages.base_page import BasePage


class LoginPage(BasePage):
    def __init__(self):
        super().__init__()
    # -------- LOGIN FORM ---------
    PARENT = Locator.xpath("//div[@data-cy='mutation-sensor']", "LOGIN_PAGE Login form")
    TXT_LOGIN_USERNAME = Locator.xpath("//input[@type='email']", "LOGIN_PAGE User name field")
    BTN_LOGIN_CONTINUE = Locator.xpath("//button[@data-element-name='universal-login-unified-auth-email-continue']"
                                       , "LOGIN_PAGE Continue button")

    def fill_email_username(self, user_name: str):
        user_name_input = self.el(self.TXT_LOGIN_USERNAME)
        user_name_input.type(user_name)

    def click_continue(self):
        cont_btn = self.el(self.BTN_LOGIN_CONTINUE).should_be(cond_enabled())
        cont_btn.click()
