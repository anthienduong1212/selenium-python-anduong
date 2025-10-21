from __future__ import annotations
from core.waiter.wait import Waiter
from core.configs.config import Configuration
from core.drivers.driver_manager import DriverManager
from core.drivers.driver_conditions import DriverCondition
from core.reports.reporting import AllureReporter


class DriverWait:
    def __init__(self, config: Configuration):
        self.waiter = Waiter(
            timeout_s=config.wait_timeout_ms / 1000.0,
            poll_s=config.polling_interval_ms / 1000.0,
        )
        self.config = config

    def until(self, *conds: DriverCondition):
        d = DriverManager.get_current_driver()

        desc = "Driver should" + ", ".join(c.name for c in conds)

        def _supplier():
            return all(c.predicate(d) for c in conds)

        def _on_timeout():
            # Find the first 'fail' condition for easier debug
            first_fail = None
            for c in conds:
                try:
                    if not c.predicate(d):
                        first_fail = c.name
                        break
                except Exception as e:
                    first_fail = f"{c.name} raise {type(e).__name__}: {e}"
            extra = f", first_failed={first_fail}" if first_fail else ""
            return f"{desc}{extra}. url={getattr(d, 'current_url',None)}, title={getattr(d, 'title', None)}"

        with AllureReporter.step(desc):
            try:
                self.waiter.until(_supplier, _on_timeout, lambda p: d.save_screenshot(p))
            except Exception as e:
                AllureReporter.attach_text("driver.url", getattr(d, "current_url", ""))
                AllureReporter.attach_text("driver.title", getattr(d, "title", ""))
                try:
                    AllureReporter.attach_page_screenshot(d, name="DriverWait Timeout")
                except Exception:
                    pass
                raise
