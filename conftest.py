import os
import re

import pytest
from dotenv import load_dotenv

load_dotenv()

from pytest import Config

from core.configuration.configuration import Configuration
from core.driver.driver_manager import DriverManager
from core.logging.logging import Logger
from core.report.reporting import AllureReporter


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
                    help="Path to configuration.json (optional)")
    group.addoption("--parallel-mode", dest="parallel_mode",
                    choices=["per-test", "per-worker", "none"],
                    default="per-test",
                    help="Parallel: per-test (each test will be ran on each browser), "
                         "per-worker (each worker uses 1 browser)")


# ================================
#          CLI PARSING
# ================================


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
    Logger.debug("Resolving browser CLI options")
    try:
        multi = config.getoption("browsers", default=None)
        single = config.getoption("browser", default=None)
        if multi:
            browsers = _flatten(multi)
            Logger.info(f"Resolved browsers: {browsers}")
            return browsers or ["chrome"]
        if single:
            Logger.info(f"Resolved single browser: {single}")
            return [str(single).strip().lower()]
    except Exception as e:
        Logger.error(f"Error resolving browser CLI options: {e}")
        raise

# ================================
#          COMMON FIXTURES
# ================================


def pytest_generate_tests(metafunc):
    if "browser_name" not in metafunc.fixturenames:
        return
    mode = metafunc.config.getoption("parallel_mode")
    if mode != "per-test":
        return
    browsers = _resolve_browser_cli(metafunc.config)
    params = [
        pytest.param(b, marks=pytest.mark.xdist_group(name=b))
        for b in browsers
    ]
    metafunc.parametrize("browser_name", params, ids=[f"browser={b}" for b in browsers])


@pytest.fixture(scope="session")
def cfg(pytestconfig):
    """Fixture provides a global configuration object for the entire session."""
    cli_path = pytestconfig.getoption("--browser-config")
    return Configuration.from_sources(cli_browser_config_path=cli_path)


@pytest.fixture(scope="session")
def browser_name(request, worker_id):
    """Determine browser name based on CLI options and parallel mode."""
    mode = request.config.getoption("parallel_mode")
    if mode == "per-test":
        return request.param

    browsers = _resolve_browser_cli(request.config)
    if mode == "per-worker":
        m = re.search(r"\d+", worker_id or "")
        idx = int(m.group()) if m else 0
        return browsers[idx % len(browsers)]
    else:
        return browsers[0]


@pytest.fixture(scope="function")
def driver(request, browser_name, cfg) -> object:
    """
    Fixture initializes and returns a driver for each test. Automatically calls DriverManager.quit_driver() when finished
    :param request:
    :param browser_name: automatically provided by the pytest_generate_tests hook
    """

    cfg.browser = browser_name

    Logger.info(f"Initializing driver for browser: {browser_name}")
    drv = DriverManager.get_driver(cfg)
    try:
        yield drv
        Logger.info(f"Driver for browser {browser_name} finished successfully.")
    except Exception as e:
        Logger.error(f"Error during driver execution: {e}")
    finally:
        try:
            DriverManager.quit_driver()
            Logger.info(f"Driver for browser {browser_name} quit successfully.")
        except Exception as e:
            Logger.error(f"Error while quitting driver: {e}")


@pytest.fixture(scope="session", autouse=True)
def _allure_env():
    AllureReporter.write_environment({
        "env": os.getenv("TEST_ENV"),
        "browser": os.getenv("BROWSER"),
        "base_url": os.getenv("BASE_URL"),
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
