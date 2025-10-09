from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Tuple, Union
from selenium.webdriver.common.by import By
from typing import Optional

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
    desc: str | None = None
    parent: Optional["Locator"] = None

    # ---------- core factories base on WebDriver -------------------
    @classmethod
    def css(cls, selector: str, desc: str | None = None) -> Locator:
        return cls(By.CSS_SELECTOR, selector, desc)

    @classmethod
    def xpath(cls, expr: str, desc: str | None = None) -> Locator:
        return cls(By.XPATH, expr, desc)

    @classmethod
    def id(cls, value: str, desc: str | None = None) -> Locator:
        return cls(By.ID, value, desc)

    @classmethod
    def name(cls, value: str, desc: str | None = None) -> Locator:
        return cls(By.NAME, value, desc)

    @classmethod
    def class_name(cls, value: str, desc: str | None = None) -> Locator:
        return cls(By.CLASS_NAME, value, desc)

    @classmethod
    def tag(cls, value: str, desc: str | None = None) -> Locator:
        return cls(By.TAG_NAME, value, desc)

    @classmethod
    def link_text(cls, text: str, desc: str | None = None) -> Locator:
        return cls(By.LINK_TEXT, text, desc)

    @classmethod
    def partial_link_text(cls, text: str, desc: str | None = None) -> Locator:
        return cls(By.PARTIAL_LINK_TEXT, text, desc)

    # -------------- Useful Builder ---------------------
    @classmethod
    def by_text(cls, text: str, desc: str | None = None) -> Locator:
        # find element with text (normalized)
        x = f".//*[normalize-space(.)={_xpath_literal(text)}]"
        return cls.xpath(x, desc or f'byText({text})')

    @classmethod
    def with_text(cls, sub: str, desc: str | None = None) -> Locator:
        x = f".//*[contains(normalize-space(.), {_xpath_literal(sub)})]"
        return cls.xpath(x, desc or f'withText({sub})')

    @classmethod
    def by_attribute(cls, attr: str, value: str | None = None, desc: str | None = None, exact: bool = True) -> Locator:
        """
        - exact=True:  [@attr='value']
        - exact=False: [contains(@attr,'value')]
        """
        if value is None:
            x = f".//*[@{attr}]"
            d = desc or f'hasAttr({attr})'
        else:
            pred = f"@{attr}={_xpath_literal(value)}" if exact else f"contains(@{attr}, {_xpath_literal(value)})"
            x = f".//*[ {pred} ]"
            d = desc or (f'attr({attr}=={value})' if exact else f'attr({attr}~{value})')
        return cls.xpath(x, d)

    @classmethod
    def attr_contains(cls, attr: str, sub: str, desc: str | None = None) -> Locator:
        return cls.by_attribute(attr, sub, desc, exact=False)

    @classmethod
    def has_class(cls, name: str, desc: str | None = None) -> Locator:
        x = f".//*[contains(concat(' ', normalize-space(@class), ' '), ' {name} ')]"
        return cls.xpath(x, desc or f'hasClass({name})')

    # ------------------ compose/chaining --------------------------
    def within(self, child: "Locator", desc: str |None = None) -> "Locator":
        """
        Create locator 'child inside self'
            - If both is xpath, linking by descendant axis
            - If parent is css, return to Locator of child **accommodate with parent*** (context-aware),
            in order to runtime using parent_we.find_element(child.by, child.value).
        :param child: Locator of child
        :param desc: description
        :return: new child locator
        """

        if self.by == By.XPATH and child.by == By.XPATH:
            p = self.value
            c = child.value.lstrip()

            c = re.sub(r"^(//|\\./|/)", "", c)
            return Locator.xpath(f"({p})//{c}", desc or f"{self.desc or ''} > {child.desc or ''}".strip(" >"))

        # If both is CSS, recommend using context-find runtime, instead of compose string
        return Locator(child.by, child.value, desc or f"{self.desc or ''} > {child.desc or ''}".strip(" >"), parent=self)

    def nth(self, index: int, desc: str | None = None) -> "Locator":
        """
        - With XPath: use `(expr)[n]` (count by filter result).
        - With CSS: use `:nth-of-type(n)` — note **count by tag (type)** not by match set.
        If you need the exact "index in match set", use `Elements.get(index)` after `find_elements(...)`
        or switch to XPath.
        :param desc: Description for element
        :param index: index of element
        :return Locator
        """
        if self.by == By.XPATH:
            return Locator.xpath(f"({self.value})[{index + 1}]", desc or f"{self.desc or ''}[{index}]")
        if self.by == By.CSS_SELECTOR:
            return Locator.css(f"{self.value}:nth-of-type({index + 1})", desc or f"{self.desc or ''}[{index}]")
        return self

    def format(self, **kwargs: Any) -> "Locator":
        if not kwargs:
            return self
        if self.by == By.XPATH:
            safe = {k: _xpath_literal(v) for k, v in kwargs.items()}
            return Locator(self.by, self.value.format(**safe), self.desc, parent=self.parent)

        return Locator(self.by,
                       self.value.format(**{k: _css_attr_value(v) for k, v in kwargs.items()}),
                       self.desc,
                       parent=self.parent)

    def __call__(self, **kwargs: Any) -> "Locator":
        return self.format(**kwargs)

    @classmethod
    def from_any(cls, selector: Union[str, ByTuple, "Locator"], desc: str | None = None) -> "Locator":
        if isinstance(selector, Locator):
            return selector.with_desc(desc) if desc else selector
        if isinstance(selector, tuple) and len(selector) == 2:
            return cls(selector[0], selector[1], desc)
        if isinstance(selector, str):

            if re.match(r"^\s*(/|//|\.)", selector):
                return cls.xpath(selector, desc)
            return cls.css(selector, desc)
        raise TypeError(f"Unsupported selector type: {type(selector)}")

    # ------------------ decs ---------------------------
    def with_desc(self, desc: str | None) -> "Locator":
        if not desc:
            return self
        return Locator(self.by, self.value, desc)

    # backward-compat cho code cũ
    def with_decs(self, desc: str) -> "Locator":
        return self.with_desc(desc)

    def __str__(self) -> str:
        return self.desc or f"{self.by}={self.value}"
