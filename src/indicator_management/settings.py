GLOBAL_INDICATOR_SAFE_NONE = True


def set_default_safe_none(state: bool) -> None:
    """
    Set up global default `none_safe`.
    """
    global GLOBAL_INDICATOR_SAFE_NONE
    GLOBAL_INDICATOR_SAFE_NONE = state


def get_default_safe_none() -> bool:
    """
    Get default `none_safe`.
    """
    return GLOBAL_INDICATOR_SAFE_NONE
