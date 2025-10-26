from __future__ import annotations
import os
from contextlib import contextmanager
from typing import Optional
from pathlib import Path

try:
    import allure
except Exception:
    class _NoAllure:
        def __getattr__(self, _):
            # Return No-op func if attribute is not existed, avoid exception if Allure absent
            return lambda *a, **k: None

        attachment_type = type("attachment_type", (), {
            "PNG": "image/png",
            "TEXT": "text/plain",
            "HTML": "text/html",
            "JSON": "application/json",
            "CSV": "text/csv",
            "XML": "application/xml",
        })

        parameter_mode = type("parameter_mode", (), {
            "DEFAULT": "default",
            "MASKED": "masked",
            "HIDDEN": "hidden",
        })
        dynamic = _NoAllure()


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
    def step(title: str):
        """Use as: with AllureReporter.step('Search hotel'): ..."""
        with allure.step(title):
            yield

    @staticmethod
    @contextmanager
    def screenshot_if_failed(driver, name: str = "Screenshot on failure"):
        """Wrap the code block: if there is an error, take a screenshot of the page and attach it to Allure."""
        try:
            yield
        except Exception:
            AllureReporter.attach_page_screenshot(driver, name=name)
            AllureReporter.attach_text("Exception", traceback.format_exc())
            raise

    # =========================
    #  ATTACHMENTS
    # =========================
    @staticmethod
    def attach_text(name: str, text: str):
        allure.attach(text, name=name, attachment_type=allure.attachment_type.TEXT)

    @staticmethod
    def attach_html(name: str, html: str):
        allure.attach(html, name=name, attachment_type=allure.attachment_type.HTML)

    @staticmethod
    def attach_json(name: str, data: Any, pretty: bool = True):
        body = json.dumps(data, ensure_ascii=False, indent=2 if pretty else None)
        allure.attach(body, name=name, attachment_type=allure.attachment_type.JSON)

    @staticmethod
    def attach_csv(name: str, csv_text: str):
        allure.attach(csv_text, name=name, attachment_type=allure.attachment_type.CSV)

    @staticmethod
    def attach_bytes(name: str, content: bytes, mime: str = "application/octet-stream"):
        allure.attach(content, name=name, attachment_type=mime)

    @staticmethod
    def attach_file(path: str | Path, name: Optional[str] = None, mime: Optional[str] = None):
        path = Path(path)
        allure.attach.file(
            str(path),
            name=name or path.name,
            attachment_type=mime or "application/octet-stream",
        )

    # ------------ Selenium Screenshots -----------------
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
        """Take a photo of 1 element and attach (PNG)."""
        try:
            # WebElement.screenshot_as_png as Selenium docs/guide
            png = getattr(element, "screenshot_as_png", None)
            if png is None:
                png = element.get_screenshot_as_png()
            allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
        except Exception as _:
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
        """Push parameters to report (displayed right below test title)."""
        for k, v in params.items():
            if k in set(mask_keys):
                allure.dynamic.parameter(k, str(v), mode=allure.parameter_mode.MASKED)
            else:
                allure.dynamic.parameter(k, v)

    # =========================
    #  ENVIRONMENT
    # =========================
    @staticmethod
    def write_environment(props: Dict[str, Any], results_dir: Optional[str] = None):
        """Write environment.properties to the allure-results directory."""
        results = Path(results_dir or os.getenv("ALLURE_RESULTS_DIR", "allure-results"))
        results.mkdir(parents=True, exist_ok=True)
        lines = []
        for k, v in props.items():
            # format .properties: key = value
            lines.append(f"{k} = {v}")
        (results / "environment.properties").write_text("\n".join(lines), encoding="utf-8")


@contextmanager
def step(title: str):
    if allure:
        with allure.step(title):
            yield
    else:
        yield


def attach_text(name: str, body: str):
    if allure:
        allure.attach(body, name, attachment_type=allure.attachment_type.TEXT)


def attach_png(name: str, path: str):
    if allure and path:
        with open(path, "rb") as f:
            allure.attach(f.read(), name, attachment_type=allure.attachment_type.PNG)
