from __future__ import annotations
import os, re
from datetime import timedelta, datetime, timezone

import mailslurp_client
from mailslurp_client import ApiClient
from core.driver.driver_manager import DriverManager

DEFAULT_TIMEOUT_MS = int(os.getenv("MAILSLURP_TIMEOUT_MS", "60000"))
OPT_REGEX = os.getenv("OTP_REGEX", r"\b(\d{6})\b")

class SlurpMailUtil:
    def __init__(self,
                 api_key: str | None = None,
                 mail_timeout_ms: int = DEFAULT_TIMEOUT_MS):
        mail_cfg = mailslurp_client.Configuration()
        mail_cfg.api_key["x-api-key"] = api_key or os.environ["MAILSLURP_API_KEY"]

        self.client = ApiClient(mail_cfg)
        self.inbox_api = mailslurp_client.InboxControllerApi(self.client)
        self.wait_api = mailslurp_client.WaitForControllerApi(self.client)
        self.mail_timeout_ms = mail_timeout_ms
        self.regex_otp = OPT_REGEX

    def create_inbox(self, expires_in_minutes: int = 30) -> tuple[str, str]:
        """Create an inbox for 1 test. Delete after N minutes"""
        opts = mailslurp_client.CreateInboxDto()
        opts.name = f"otp_{datetime.now(timezone.utc).isoformat()}"
        opts.expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        inbox = self.inbox_api.create_inbox_with_options(opts)
        return inbox.id, inbox.email_address

    def wait_for_otp(self,
                     inbox_id: str,
                     subject_contains: str | None = None,
                     unread_only: bool = True) -> str:
        """Wait for email and get the OTP"""
        if subject_contains:
            match = mailslurp_client.MatchOptions(
                matches=[
                    mailslurp_client.MatchOption(field="SUBJECT", should="CONTAIN", value=subject_contains)
                ]
            )

            emails = self.wait_api.wait_for_matching_emails(inbox_id=inbox_id,
                                                            timeout=self.mail_timeout_ms,
                                                            unread_only=unread_only,
                                                            match_options=match,
                                                            count=1)
            email = emails[0]

        else:
            email = self.wait_api.wait_for_latest_email(inbox_id=inbox_id,
                                                        timeout=self.mail_timeout_ms,
                                                        unread_only=unread_only)

        body = (email.body or email.text or "")
        m = re.search(self.regex_otp, body)
        if not m:
            raise AssertionError(f"Unable to get OTP in {email.id}")
        return m.group(1)
