from typing import Dict, Type

from core.driver.providers.browser_provider import BrowserProvider

_PROVIDER_REGISTRY: Dict[str, Type[BrowserProvider]] = {}


def register_provider(provider_cls: Type[BrowserProvider]):
    name = provider_cls.name
    if not name:
        raise ValueError("Provider must define 'name' attribute")

    _PROVIDER_REGISTRY[name.lower()] = provider_cls

    for a in getattr(provider_cls, "aliases", []):
        _PROVIDER_REGISTRY[a.lower()] = provider_cls
    return provider_cls


def get_provider_class(name: str):
    return _PROVIDER_REGISTRY.get(name.lower())


def discover_and_register(package: str) -> None:
    import pkgutil, importlib
    pkg = importlib.import_module(package)
    for finder, modname, ispkg in pkgutil.iter_modules(pkg.__path__):
        importlib.import_module(f"{package}.{modname}")
