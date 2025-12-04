from __future__ import annotations
import allure
from typing import List
from core.element.conditions import Condition
from core.element.conditions import clickable as cond_clickable
from core.element.conditions import visible as cond_visible
from core.element.locator import Locator
from core.utils.browser_utils import BrowserUtils
from core.utils.slurp_mail_utils import SlurpMailUtil
from core.utils.string_utils import extract_email_address
from pages.base_page import BasePage
from pages.agoda.enums.mail_subject import MailSubject


class LoginPage(BasePage):
    def __init__(self):
        super().__init__()

    # -------- LOGIN FORM ---------
    _IFRAME_LOGIN_FORM = Locator.xpath("//iframe[@data-cy='ul-app-frame']", "HOMEPAGE Login iframe")
    _FORM_LOGIN_PARENT = Locator.xpath("//div[@id='root']/div[@data-cy='mutation-sensor']", "LOGIN_PAGE Login form")
    _TXT_LOGIN_USERNAME = Locator.xpath("//input[@type='email']", "LOGIN_PAGE User name field")
    _BTN_LOGIN_CONTINUE = Locator.xpath("//button[@data-element-name='universal-login-unified-auth-email-continue']"
                                        , "LOGIN_PAGE Login form continue button")

    # -------- OTP FORM -----------
    _TXT_FORM_SUB_HEADING = Locator.xpath("//div[@data-cy='form-sub-heading']/p", "LOGIN_PAGE OTP form sub heading")
    _TXT_OTP_BOX = Locator.xpath("//input[@data-cy={index}]", "LOGIN_PAGE 6 digits OTP fill box")
    _BTN_OTP_FORM_CONTINUE = Locator.xpath("//button[@data-element-name='universal-login-unified-auth-otp-continue']"
                                                                 , "LOGIN_PAGE OTP form continue button")

    @allure.step("Switch to iframe")
    def switch_to_login_inframe(self):
        iframe = self.el(self._IFRAME_LOGIN_FORM).should_be(cond_visible())
        iframe.switch_to_frame()

    @allure.step("Wait for Login form display")
    def wait_login_form_display(self) -> "Element":
        return self.el(self._FORM_LOGIN_PARENT).should_be(cond_visible())

    @allure.step("Fill username: {user_name}")
    def fill_email_username(self, user_name: str):
        user_name_input = self.wait_login_form_display().find(self._TXT_LOGIN_USERNAME)
        user_name_input.type(user_name)

    @allure.step("Wait for LOGIN button enable")
    def wait_login_button(self) -> "Element":
        return self.el(self._BTN_LOGIN_CONTINUE).should_be(cond_clickable())

    @allure.step("Wait for OTP Submit button enable")
    def wait_otp_submit_button(self) -> "Element":
        return self.el(self._BTN_OTP_FORM_CONTINUE).should_be(cond_clickable())

    @allure.step("Click LOGIN button")
    def click_continue(self):
        cont_btn = self.wait_login_button()
        cont_btn.click()

    @allure.step("Click OTP form button")
    def click_otp_form_continue(self):
        cont_btn = self.wait_otp_submit_button()
        cont_btn.click()

    @allure.step("Login with username : {user_name}")
    def login(self, user_name: str):
        self.switch_to_login_inframe()
        self.fill_email_username(user_name)
        self.click_continue()

    @allure.step("Wait for OTP send to email {email}")
    def get_otp_from_mail(self, mail_box: SlurpMailUtil, inbox_id: str, email: str) -> str:
        subject = MailSubject.OTP_MAIL_SUBJECT
        return mail_box.wait_for_otp(inbox_id, subject)

    @allure.step("Get email display on input OTP form")
    def get_email_from_otp_form(self) -> str:
        sub_heading = self.el(self._TXT_FORM_SUB_HEADING).should_be(cond_visible())
        return extract_email_address(sub_heading.text())

    @allure.step("Input OTP to field")
    def type_otp_digits(self, otp: int):
        parent = self.wait_login_form_display()
        index: int = 0

        for digit in list(otp):
            opt_box = parent.find(self._TXT_OTP_BOX(index=f"otp-box-{index}"))
            opt_box.type(digit)
            index = index + 1

    @allure.step("Submit OTP from email {email}")
    def submit_otp_from_email(self, mail_box: SlurpMailUtil, inbox_id: str, email: str):
        otp = self.get_otp_from_mail(mail_box, inbox_id, email)

        self.type_otp_digits(otp)
        self.click_otp_form_continue()








