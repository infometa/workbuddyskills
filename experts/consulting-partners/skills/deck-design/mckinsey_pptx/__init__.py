__version__ = "0.2.0"


def __getattr__(name):
    if name in ("PresentationBuilder", "build_from_spec"):
        from .builder import PresentationBuilder, build_from_spec
        return {"PresentationBuilder": PresentationBuilder,
                "build_from_spec": build_from_spec}[name]
    if name in ("Theme", "DEFAULT_THEME"):
        from .theme import Theme, DEFAULT_THEME
        return {"Theme": Theme, "DEFAULT_THEME": DEFAULT_THEME}[name]
    raise AttributeError(name)
