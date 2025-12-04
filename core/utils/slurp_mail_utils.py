from __future__ import annotations

import os
import re
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

import mailslurp_client
from mailslurp_client import ApiClient, Configuration
from mailslurp_client.api.inbox_controller_api import InboxControllerApi
from mailslurp_client.models import CreateInboxDto

from core.logging.logging import Logger
from core.constants.constants import Constants

DEFAULT_TIMEOUT_MS = int(os.getenv("MAILSLURP_TIMEOUT_MS", "60000"))
OPT_REGEX = os.getenv("OTP_REGEX", r"OTP is (\d{6})")


class SlurpMailUtil:
    def __init__(self,
                 api_key: str | None = None,
                 mail_timeout_ms: int = DEFAULT_TIMEOUT_MS):

        mail_cfg = mailslurp_client.Configuration()
        mail_cfg.api_key["x-api-key"] = api_key

        self.client = ApiClient(mail_cfg)
        self.inbox_api = mailslurp_client.InboxControllerApi(self.client)
        self.wait_api = mailslurp_client.WaitForControllerApi(self.client)
        self.mail_timeout_ms = mail_timeout_ms or Constants.LONG_DURATION_MS
        self.regex_otp = OPT_REGEX

    def list_active_inbox(self, name_prefix: Optional[str] = None) -> List[Tuple[str, str]]:
        """Returns (id, email) inboxes that have not expired (expiresAt None or > now),
            can be filtered by name prefix (eg: 'otp_')."""
        page = 0
        active: List[Tuple[str, str]] = []

        while True:
            page_result = self.inbox_api.get_all_inboxes(page=page, size=50, sort="DESC")
            for dto in page_result.content:
                if (name_prefix is None) or (dto.name or "").startswith(name_prefix):
                    active.append((str(dto.id), str(dto.email_address)))
            # pagination
            if page >= (page_result.total_pages - 1):
                break
            page += 1
        return active

    def create_inbox(self) -> tuple[str, str]:
        """Create an inbox for 1 test. Delete after N minutes"""

        candidates = self.list_active_inbox(name_prefix="otp_")
        if candidates:
            inbox_id, email_addr = candidates[0]
            Logger.info(f"Found active inbox email: {email_addr} and inbox_id: {inbox_id}")
            return candidates[0]

        opts = CreateInboxDto()
        opts.name = f"otp_{datetime.now(timezone.utc).isoformat()}"
        inbox = self.inbox_api.create_inbox_with_options(opts)
        Logger.info(f"Inbox created successful with ID: {inbox.id} and email: {inbox.email_address}")
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
        if email:
            Logger.info(f"Found email with subject: {subject_contains}. Fetching full email body.")
            email_full = self.inbox_api.get_latest_email_in_inbox(inbox_id, self.mail_timeout_ms)
            body = (email_full.body or email_full.text or "")
            m = re.search(self.regex_otp, body)
            if not m:
                raise AssertionError(f"Unable to get OTP in {email.id}")
            return m.group(1)
        else:
            Logger.error("Email not found !")
