from __future__ import annotations
import os, json, traceback
from contextlib import contextmanager
from typing import Optional
from pathlib import Path
from allure_commons.types import AttachmentType, ParameterMode
from tempfile import NamedTemporaryFile

try:
    import allure
except Exception:
    class _NoAllure:
        def __getattr__(self, _):
            # Return No-op func if attribute is not existed, avoid exception if Allure absent
            return lambda *a, **k: None

        class AttachmentType:
            PNG = "image/png"
            TEXT = "text/plain"
            HTML = "text/html"
            JSON = "application/json"
            CSV = "text/csv"
            XML = "application/xml"

        class ParameterMode:
            DEFAULT = "default"
            MASKED = "masked"
            HIDDEN = "hidden"

        dynamic = type("D", (), {"title": lambda *a, **k: None,
                                 "description": lambda *a, **k: None,
                                 "tag": lambda *a, **k: None,
                                 "severity": lambda *a, **k: None,
                                 "epic": lambda *a, **k: None,
                                 "feature": lambda *a, **k: None,
                                 "story": lambda *a, **k: None,
                                 "link": lambda *a, **k: None,
                                 "issue": lambda *a, **k: None,
                                 "testcase": lambda *a, **k: None,
                                 "parameter": lambda *a, **k: None})()


    allure = _NoAllure()


class AllureReporter:
    """A neat utility class to:
    - Record step/attach content (text/json/html/csv/file/screenshot)
    - Add dynamic metadata: title, tag, severity, epic/feature/story, link/issue/tms
    - Record parameters (mask if needed)
    - Take screenshot automatically when code block/step fails
    - Record environment.properties for report
    """

    # =========================
    #  STEPS (context wrapper)
    # =========================
    @staticmethod
    @contextmanager
    def step(title: str, driver=None, included_context: bool = True):
        """Use as: with AllureReporter.step('Search hotel'): block..."""
        with allure.step(title):
            try:
                yield
            except Exception:
                if driver is not None:
                    AllureReporter.attach_page_screenshot(driver)
                    if include_context:
                        AllureReporter.attach_text("URL", safe_str(getattr(driver, "current_url", "")))
                        AllureReporter.attach_text("Title", safe_str(getattr(driver, "title", "")))
                        # console logs (if supported)
                        try:
                            logs = getattr(driver, "get_log", lambda *_: [])("browser")
                            AllureReporter.attach_json("Console logs", logs)
                        except Exception:
                            pass
                AllureReporter.attach_text("Exception", traceback.format_exc())
                raise

    # =========================
    #  ATTACHMENTS
    # =========================
    @staticmethod
    def attach_text(name: str, text: str):
        allure.attach(text or "", name=name, attachment_type=AttachmentType.TEXT)

    @staticmethod
    def attach_html(name: str, html: str):
        allure.attach(html or "", name=name, attachment_type=AttachmentType.HTML)

    @staticmethod
    def attach_json(name: str, data: Any, pretty: bool = True):
        body = json.dumps(data, ensure_ascii=False, indent=2 if pretty else None)
        allure.attach(body, name=name, attachment_type=AttachmentType.JSON)

    @staticmethod
    def attach_bytes(name: str, content: bytes, attachment_type: Any = AttachmentType.TEXT):
        allure.attach(content, name=name, attachment_type=attachment_type)

    @staticmethod
    def attach_file(path: str | Path, name: Optional[str] = None,
                    attachment_type: Any = None, extension: Optional[str] = None):
        # Allure accepts attachment_type or extension for correct preview
        path = Path(path)
        allure.attach.file(str(path), name=name or path.name,
                           attachment_type=attachment_type, extension=extension)

    # =========================
    #    SELENIUM SCREENSHOT
    # =========================
    @staticmethod
    def attach_page_screenshot(driver, name: str = "Page Screenshot"):
        """Take a full screenshot of the current page (PNG) and attach it (no need to write the file)."""
        try:
            png = driver.get_screenshot_as_png()  # Selenium API
            allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
        except Exception as _:
            pass

    @staticmethod
    def attach_element_screenshot(element, name: str = "Element Screenshot"):
        try:
            # Element API: screenshot_as_png OR screenshot("file")
            png = getattr(element, "screenshot_as_png", None)
            if png is None:
                # fallback: write to temp file via element.screenshot(...)
                with NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    element.screenshot(tmp.name)
                    AllureReporter.attach_file(tmp.name, name=name, attachment_type=AttachmentType.PNG)
            else:
                allure.attach(png, name=name, attachment_type=AttachmentType.PNG)
        except Exception:
            pass

    # =========================
    #  METADATA (dynamic)
    # =========================

    @staticmethod
    def set_title(title: str):
        allure.dynamic.title(title)

    @staticmethod
    def set_description(md_text: str):
        allure.dynamic.description(md_text)

    @staticmethod
    def add_tags(*tags: str):
        allure.dynamic.tag(*tags)

    @staticmethod
    def set_severity(level: str):  # "trivial" | "minor" | "normal" | "critical" | "blocker"
        allure.dynamic.severity(level)

    @staticmethod
    def set_behavior(epic: Optional[str] = None, feature: Optional[str] = None, story: Optional[str] = None):
        if epic:
            allure.dynamic.epic(epic)
        if feature:
            allure.dynamic.feature(feature)
        if story:
            allure.dynamic.story(story)

    @staticmethod
    def add_link(url: str, name: Optional[str] = None, link_type: str = "link"):
        allure.dynamic.link(url, name=name, link_type=link_type)

    @staticmethod
    def add_issue(id_or_url: str, name: Optional[str] = None):
        allure.dynamic.issue(id_or_url, name=name)

    @staticmethod
    def add_tms(id_or_url: str, name: Optional[str] = None):
        allure.dynamic.testcase(id_or_url, name=name)

    # =========================
    #  PARAMETERS
    # =========================
    @staticmethod
    def add_parameters(params: Dict[str, Any], mask_keys: Iterable[str] = ()):
        masked = set(mask_keys or ())
        for k, v in (params or {}).items():
            mode = ParameterMode.MASKED if k in masked else ParameterMode.DEFAULT
            allure.dynamic.parameter(k, str(v) if v is not None else "", mode=mode)

    # =========================
    #  ENVIRONMENT
    # =========================
    @staticmethod
    def write_environment(props: Dict[str, Any], results_dir: Optional[str] = None):
        """Write environment.properties to the allure-results directory."""
        results = Path(results_dir or os.getenv("ALLURE_RESULTS_DIR", "allure-results"))
        results.mkdir(parents=True, exist_ok=True)
        lines = [f"{k} = {v}" for k, v in (props or {}).items()]
        (results / "environment.properties").write_text("\n".join(lines), encoding="utf-8")


def safe_str(x: Any) -> str:
    try:
        return str(x)
    except Exception:
        return ""
