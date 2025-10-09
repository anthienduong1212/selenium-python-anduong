import pytest
from pathlib import Path
import json
from core.configs.config import Configuration
from core.drivers.driver_manager import DriverManager


def pytest_addoption(parser):
    """
    Add command line options for pytest:
    --browser: browser name (chrome, firefox, edge…)
    --headless: true/false run headless mode
    --remote-url: Selenium Grid URL (if using remote)
    --browser-config: JSON file path override capabilities
    --browsers: allow passing multiple browsers (test parameterization)
    """
    group = parser.getgroup("selenium")

    group.addoption("--browser", action="store", default=None,
                    choices=["chrome", "firefox", "edge"],
                    help="Single browser to run")
    group.addoption("--browsers", action="append", default=None,
                    choices=["chrome", "firefox", "edge"],
                    help="Repeat to run on multiple browsers")
    group.addoption("--headless", action="store_true", default=False,
                    help="Run browsers in headless mode")
    group.addoption("--remote-url", action="store", default=None,
                    help="Selenium Grid URL, e.g. http://127.0.0.1:4444/wd/hub")

    group.addoption("--browser-config", action="store", default=None,
                    help="Path to browsers.json (optional)")


def _detect_browser_from_json(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        data = json.load(p.read_text(encoding="utf-8"))
        return list(data.keys())
    except Exception:
        return []

def pytest_generate_tests(metafunc):
    if "browser_name" in metafunc.fixturenames:
        cfg_json = metafunc.config.getoption("--browser-config")

        single = metafunc.config.getoption("--browser")          # "chrome" | None
        multi  = metafunc.config.getoption("--browsers")         # ["chrome", "firefox"] | None

        def _detect_browser_from_json(path: str) -> list[str]:
            from pathlib import Path
            import json
            p = Path(path) if path else None
            if not p or not p.exists():
                return []
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                return list(data.keys())
            except Exception:
                return []

        if multi:
            browsers = multi
        elif single:
            browsers = [single]
        else:
            from_json = _detect_browser_from_json(cfg_json)
            browsers = from_json or ["chrome"]

        metafunc.parametrize("browser_name", browsers, scope="session")


@pytest.fixture(scope="function")
def driver(request, browser_name) -> object:
    """
    Fixture initializes and returns a driver for each test. Automatically calls DriverManager.quit_driver() when finished.
    :param browser_name: automatically provided by the pytest_generate_tests hook
    """
    cfg = Configuration()
    cfg.browser = browser_name
    headless = request.config.getoption("--headless")
    if headless is not None:
        cfg.headless = str(headless).lower() == "true"

    remote = request.config.getoption("--remote-url")
    if remote:
        cfg.remote_url = remote

    cfg_json = request.config.getoption("--browser-config")
    if cfg_json:
        cfg.load_browser_json(cfg_json)

    drv = DriverManager.get_driver(cfg)
    drv.config = cfg
    yield drv
    DriverManager.quit_driver()
