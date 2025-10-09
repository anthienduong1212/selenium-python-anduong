from __future__ import annotations
from core.waiter.wait import Waiter
from core.configs.config import Configuration
from core.drivers.driver_manager import DriverManager
from core.drivers.driver_conditions import DriverCondition
from core.reports.reporting import step, attach_text


class DriverWait:
    def __init__(self, config: Configuration):
        self.waiter = Waiter(
            timeout_s=config.timeout_ms / 1000.0,
            poll_s=config.polling_interval_ms / 1000.0,
        )
        self.config = config

    def until(self, *conds: DriverCondition):
        d = DriverManager.get_driver(self.config)
        # d = DriverManager.get_current_driver()

        desc = "Driver should" + ", ".join(c.name for c in conds)

        def _supplier():
            return all(c.predicate(d) for c in conds)

        def _on_timeout():
            return f"{desc}. url={getattr(d,'current_url',None)}, title={getattr(d,'title',None)}"

        with step(desc):
            try:
                self.waiter.until(_supplier, _on_timeout, lambda p: d.save_screenshot(p))
            except Exception as e:
                attach_text("driver.url", getattr(d, "current_url", ""))
                attach_text("driver.title", getattr(d, "title", ""))
                raise