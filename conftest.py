import re
import pytest
import json
import os
from pathlib import Path
from core.configuration.configuration import Configuration
from core.driver.driver_manager import DriverManager
from core.report.reporting import AllureReporter
from core.utils.slurp_mail_utils import SlurpMailUtil
from pytest import Config
from typing import List

from dotenv import load_dotenv
load_dotenv()


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
    group.addoption("--browsers", nargs="+", action="append", default=None,
                    choices=["chrome", "firefox", "edge"],
                    help="Repeat to run on multiple browsers, or pass 'auto' to read from --browser-config")
    group.addoption("--remote-url", dest="remote_url", action="store", default=None,
                    help="Selenium Grid URL, e.g. http://127.0.0.1:4444/wd/hub")
    group.addoption("--browser-config", dest="browser_config", action="store", default=None,
                    help="Path to config.json (optional)")
    group.addoption("--parallel-mode", dest="parallel_mode",
                    choices=["per-test", "per-worker", "none"],
                    default="per-test",
                    help="Parallel: per-test (each test will be ran on each browser), "
                         "per-worker (each worker uses 1 browser)")


def _flatten(items):
    out, seen = [], set()
    for it in items or []:
        if isinstance(it, (list, tuple)):
            for x in it:
                x = str(x).strip().lower()
                if x and x not in seen: out.append(x); seen.add(x)
        else:
            x = str(it).strip().lower()
            if x and x not in seen: out.append(x); seen.add(x)
    return out


def _resolve_browser_cli(config: Config) -> list[str]:
    multi = config.getoption("browsers", default=None)
    single = config.getoption("browser", default=None)
    if multi:
        lst = _flatten(multi)
        return lst or ["chrome"]
    if single:
        return [str(single).strip().lower()]


def pytest_generate_tests(metafunc):
    if "browser_name" not in metafunc.fixturenames:
        return

    mode = metafunc.config.getoption("parallel_mode")
    if mode != "per-test":
        # per-test/none: DON'T parameterize here
        return

    browsers = _resolve_browser_cli(metafunc.config)

    # Assign mark xdist_group by browser name to gather by worker when using --dist=loadgroup
    # If b is browser name in list, mark this test name = browser

    params = [
        pytest.param(b, marks=pytest.mark.xdist_group(name=b))
        for b in browsers
    ]

    metafunc.parametrize("browser_name", params, ids=[f"browser={b}" for b in browsers])


@pytest.fixture(scope="session")
def cfg(pytestconfig):
    return Configuration.from_cli_file(pytestconfig.getoption("--browser-config"))


@pytest.fixture(scope="session")
def browser_name(request, worker_id):
    mode = request.config.getoption("parallel_mode")
    if mode == "per-test":
        # return value from parameterize
        return request.param

    # if mode is "per-worker" or none
    browsers = _resolve_browser_cli(request.config)
    if mode == "per-worker":
        m = re.search(r"\d+", worker_id or "")
        idx = int(m.group()) if m else 0
        return browsers[idx % len(browsers)]
    else:
        return browsers[0]


@pytest.fixture(scope="function")
def driver(request, browser_name) -> object:
    """
    Fixture initializes and returns a driver for each test. Automatically calls DriverManager.quit_driver() when finished
    :param request:
    :param browser_name: automatically provided by the pytest_generate_tests hook
    """
    cli_cfg_path = request.config.getoption("--browser-config", default=None)
    cfg = Configuration.from_cli_file(cli_cfg_path)
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


@pytest.fixture()
def otp_mailbox():
    ms = SlurpMailUtil(api_key=os.getenv("MAILSLURP_API_KEY"))
    inbox_id, email_addr = ms.create_inbox(expires_in_minutes=30)
    yield {"ms": ms, "inbox_id": inbox_id, "email": email_addr}


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
