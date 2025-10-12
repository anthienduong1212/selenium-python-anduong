import pytest
import json
import os

from pathlib import Path
from core.configs.config import Configuration
from core.drivers.driver_manager import DriverManager
from core.reports.reporting import AllureReporter


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
                    help="Repeat to run on multiple browsers, or pass 'auto' to read from --browser-config")
    group.addoption("--headless", action="store_true", default=False,
                    help="Run browsers in headless mode")
    group.addoption("--remote-url", dest="remote_url", action="store", default=None,
                    help="Selenium Grid URL, e.g. http://127.0.0.1:4444/wd/hub")

    group.addoption("--browser-config", dest="browser_config", action="store", default=None,
                    help="Path to browsers.json (optional)")


def _detect_browser_from_json(path: str) -> list[str]:
    p = Path(path) if path else None
    if not p or not p.exists():
        return []

    data = json.load(p.read_text(encoding="utf-8"))

    # if browsers is not exist in data, get() will create it assign the whole data to it
    browsers = data.get("browsers", data)
    if not isinstance(browsers, dict):
        return []
    return sorted(browsers.keys())


def pytest_generate_tests(metafunc):
    if "browser_name" not in metafunc.fixturenames:
        return

    multi = metafunc.config.getoption("browsers")
    single = metafunc.config.getoption("browser")

    if multi and "auto" in multi:
        cfg_json = metafunc.config.getoption("browser_config")
        auto_list = _detect_browser_from_json(cfg_json)
        # Fallback: if null, using single or chrome
        params = auto_list or ([single] if single else ["chrome"])
    elif multi:
        params = multi
    else:
        params = [single] if single else ["chrome"]

    metafunc.parametrize("browser_name", params, ids=params)


@pytest.fixture(scope="function")
def driver(request, browser_name) -> object:
    """
    Fixture initializes and returns a driver for each test. Automatically calls DriverManager.quit_driver() when finished.
    :param request:
    :param browser_name: automatically provided by the pytest_generate_tests hook
    """
    cfg = Configuration.from_pytest_options(request.config)
    cfg.browser = browser_name
    drv = DriverManager.get_driver(cfg)
    try:
        yield drv
    finally:
        try:
            DriverManager.quit_driver()
        except Exception:
            pass


@pytest.fixture(scope="session", autouse=True)
def _allure_env():
    AllureReporter.write_environment({
        "env": os.getenv("TEST_ENV", "local"),
        "browser": os.getenv("BROWSER", "chrome"),
        "base_url": os.getenv("BASE_URL", "https://www.agoda.com"),
    })


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        drv = item.funcargs.get("driver")
        if drv:
            try:
                AllureReporter.attach_page_screenshot(drv, name=f"{item.name} - failed")
            except Exception:
                pass
