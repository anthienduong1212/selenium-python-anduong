from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import mailslurp_client
from mailslurp_client import ApiClient, Configuration
from mailslurp_client.api.inbox_controller_api import InboxControllerApi
from mailslurp_client.models import CreateInboxDto

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

    def list_active_inbox(self, name_prefix: Optional[str] = None) -> List[Tuple[str, str]]:
        """Returns (id, email) inboxes that have not expired (expiresAt None or > now),
            can be filtered by name prefix (eg: 'otp_')."""
        page = 0
        active: List[Tuple[str, str]] = []
        now = datetime.now(timezone.utc)

        while True:
            page_result = self.inbox_api.get_all_inboxes(page=page, size=50, sort="DESC")
            for dto in page_result.content:
                # dto.expires_at là ISO 8601 hoặc None
                exp = dto.expires_at
                still_valid = (exp is None) or (exp > now)
                name_ok = (name_prefix is None) or (dto.name or "").startswith(name_prefix)
                if still_valid and name_ok:
                    active.append((str(dto.id), str(dto.email_address)))
            # pagination
            if page >= (page_result.total_pages - 1):
                break
            page += 1
        return active

    def create_inbox(self, expires_in_minutes: int = 30) -> tuple[str, str]:
        """Create an inbox for 1 test. Delete after N minutes"""

        # Find an active inbox with active prefix "otp_"
        candidates = self.list_active_inbox(name_prefix="otp_")
        if candidates:
            return candidates[0]

        opts = CreateInboxDto()
        opts.name = f"otp_{datetime.now(timezone.utc).isoformat()}"
        opts.expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)
        inbox = self.inbox_api.create_inbox_with_options(opts)
        return str(inbox.id), str(inbox.email_address)

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
