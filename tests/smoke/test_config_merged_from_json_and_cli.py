# run the test by "pytest -q -n auto --browser-config configs/browsers.json --browsers chrome --browsers firefox"

from core.configs.config import Configuration


def test_config_merged_from_json_and_cli(pytestconfig):
    cfg = Configuration.from_pytest_options(pytestconfig)

    assert cfg.browser in {"chrome", "firefox", "edge"}
    assert isinstance(cfg.wait_timeout_ms, int) and cfg.wait_timeout_ms > 0
