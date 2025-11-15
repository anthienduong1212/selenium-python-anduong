from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Tuple, Union, Optional, Any   # + Any
from selenium.webdriver.common.by import By

ByTuple = Tuple[str, str]

# ----------- helpers: safe escape -------------
def _xpath_literal(s: str) -> str:
    s = str(s)
    if "'" not in s:
        return f"'{s}'"
    if '"' not in s:
        return f'"{s}"'

    parts = [f"'{chunk}'" for chunk in s.split("'")]
    return f"concat({', '"'\\''"', '.join(parts)})"

def _css_attr_value(s: str) -> str:
    return re.sub(r'[\\.#! "\[\]:]', lambda match: '\\' + match.group(0), str(s))

@dataclass(frozen=True)
class Locator:
    by: str
    value: str
    desc: Optional[str] = None
    parent: Optional["Locator"] = None

    # ---------- core factories base on WebDriver -------------------
    @classmethod
    def css(cls, selector: str, desc: Optional[str] = None) -> "Locator":
        return cls(By.CSS_SELECTOR, selector, desc)

    @classmethod
    def xpath(cls, expr: str, desc: Optional[str] = None) -> "Locator":
        return cls(By.XPATH, expr, desc)

    @classmethod
    def id(cls, value: str, desc: Optional[str] = None) -> "Locator":
        return cls(By.ID, value, desc)

    @classmethod
    def name(cls, value: str, desc: Optional[str] = None) -> "Locator":
        return cls(By.NAME, value, desc)

    @classmethod
    def class_name(cls, value: str, desc: Optional[str] = None) -> "Locator":
        return cls(By.CLASS_NAME, value, desc)

    @classmethod
    def tag(cls, value: str, desc: Optional[str] = None) -> "Locator":
        return cls(By.TAG_NAME, value, desc)

    @classmethod
    def link_text(cls, text: str, desc: Optional[str] = None) -> "Locator":
        return cls(By.LINK_TEXT, text, desc)

    @classmethod
    def partial_link_text(cls, text: str, desc: Optional[str] = None) -> "Locator":
        return cls(By.PARTIAL_LINK_TEXT, text, desc)

    # ------------------ factory ----------------------------------
    @classmethod
    def by_text(cls, text: str, desc: Optional[str] = None) -> "Locator":
        x = f".//*[normalize-space(.)={_xpath_literal(text)}]"
        return cls.xpath(x, desc or f'byText({text})')

    @classmethod
    def with_text(cls, sub: str, desc: Optional[str] = None) -> "Locator":
        x = f".//*[contains(normalize-space(.), {_xpath_literal(sub)})]"
        return cls.xpath(x, desc or f'withText({sub})')

    # ------------------ compose/chaining --------------------------
    def within(self, child: "Locator", desc: Optional[str] = None) -> "Locator":
        """
        Create locator 'child inside self'.
        - If both are XPath: join by descendant axis.
        - Otherwise: return locator child with self as parent (for runtime use parent_we.find_element()).
        """
        if self.by == By.XPATH and child.by == By.XPATH:
            p = self.value
            c = child.value
            if c.startswith("//"):
                c = "." + c
            return Locator.xpath(
                f"{p}//{c.lstrip('./')}",
                desc or f"{self.desc or ''} > {child.desc or ''}".strip(" >")
            )
        return Locator(
            child.by, child.value,
            desc or f"{self.desc or ''} > {child.desc or ''}".strip(" >"),
            parent=self
        )

    def format(self, **kwargs: Any) -> "Locator":
        if not kwargs:
            return self
        if self.by == By.XPATH:
            safe = {k: _xpath_literal(v) for k, v in kwargs.items()}
            return Locator(self.by, self.value.format(**safe), self.desc, parent=self.parent)

    def __call__(self, **kwargs: Any) -> "Locator":
        return self.format(**kwargs)

    # ------------------ desc ---------------------------
    def with_desc(self, desc: Optional[str]) -> "Locator":
        if not desc:
            return self
        return Locator(self.by, self.value, desc, parent=self.parent)
