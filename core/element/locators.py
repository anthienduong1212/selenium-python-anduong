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
    parts = []
    for chunks in s.split("'"):
        parts.append(f"'{chunks}'")
        parts.append('"\'"')
    parts = parts[:-1]
    return f"concat({','.join(parts)})"

def _css_attr_value(s: str) -> str:
    # Simple escape for css value
    return str(s).replace("\\", "\\\\").replace('"', '\\"')

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
        # exact text, normalize space như Selenide byText
        x = f".//*[normalize-space(.)={_xpath_literal(text)}]"
        return cls.xpath(x, desc or f'byText({text})')

    @classmethod
    def with_text(cls, sub: str, desc: Optional[str] = None) -> "Locator":
        # substring, ignore whitespace like Selenide withText
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
        # context-aware: Let resolver use search context of Selenium
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
        # CSS: escape để tránh vỡ selector khi có " hoặc \
        return Locator(
            self.by,
            self.value.format(**{k: _css_attr_value(v) for k, v in kwargs.items()}),
            self.desc,
            parent=self.parent
        )

    def __call__(self, **kwargs: Any) -> "Locator":
        return self.format(**kwargs)

    @classmethod
    def from_any(cls, selector: Union[str, ByTuple, "Locator"], desc: Optional[str] = None) -> "Locator":
        if isinstance(selector, Locator):
            return selector.with_desc(desc) if desc else selector
        if isinstance(selector, tuple) and len(selector) == 2:
            return cls(selector[0], selector[1], desc)
        if isinstance(selector, str):
            if re.match(r"^\s*(/|//|\.)", selector):
                return cls.xpath(selector, desc)
            return cls.css(selector, desc)
        raise TypeError(f"Unsupported selector type: {type(selector)}")

    # ------------------ desc ---------------------------
    def with_desc(self, desc: Optional[str]) -> "Locator":
        if not desc:
            return self
        # GIỮ parent để không mất context-find
        return Locator(self.by, self.value, desc, parent=self.parent)
