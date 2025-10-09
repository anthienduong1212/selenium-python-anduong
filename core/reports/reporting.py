from __future__ import annotations
from contextlib import contextmanager
from typing import Optional

try:
    import allure
except Exception:
    allure = None


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
