"""Shared lightweight helpers (no heavy imports to avoid circular deps)."""


def clamp_float(value: object, default: float = 0.0, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp a value to a range, coercing to float with a fallback default."""
    try:
        v = float(value)
    except Exception:
        v = float(default)
    if v < lo:
        return float(lo)
    if v > hi:
        return float(hi)
    return float(v)
