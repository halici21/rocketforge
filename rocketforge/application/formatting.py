"""Engineering number formatting.

One formatter for the whole application, so a value looks the same wherever it
appears and the rules live in a single testable place rather than being
reinvented per page (task section 18).

Formatting never touches the numbers themselves: the physics layer computes at
full double precision, results are stored numerically, and rounding happens
only on the way to the screen.
"""

from __future__ import annotations

import math

__all__ = ["format_engineering", "EM_DASH", "significant_digits_of"]

#: What a value that does not exist is rendered as. Never a zero, never a blank.
EM_DASH = "—"

#: Outside this band a fixed-point rendering is either unreadably long or
#: loses the magnitude entirely, so scientific notation is clearer.
_SCIENTIFIC_LOWER = 1e-4
_SCIENTIFIC_UPPER = 1e6


def format_engineering(value: float | None, significant: int = 6) -> str:
    """Render a number the way an engineer expects to read it.

    Fixed point for ordinary magnitudes, scientific notation only where fixed
    point would be worse: ``1.68750`` stays as it is, while ``1.32e-13`` does
    not become ``0.000000000000132``.

    Args:
        value: The number, or None for a quantity that does not apply.
        significant: Significant digits to show, 3 to 12.

    Returns:
        The formatted string, or an em dash for None and non-finite values.
    """
    if value is None:
        return EM_DASH
    try:
        number = float(value)
    except (TypeError, ValueError):
        return EM_DASH
    if not math.isfinite(number):
        return EM_DASH

    significant = max(3, min(12, int(significant)))
    if number == 0.0:
        return f"{0.0:.{significant - 1}f}"

    magnitude = abs(number)
    if magnitude < _SCIENTIFIC_LOWER or magnitude >= _SCIENTIFIC_UPPER:
        text = f"{number:.{significant - 1}e}"
        # Trim the exponent to the shortest unambiguous form: 1.23e-13, not
        # 1.23e-013, and drop a redundant plus.
        mantissa, exponent = text.split("e")
        sign = "-" if exponent[0] == "-" else ""
        return f"{mantissa}e{sign}{int(exponent[1:])}"

    # Fixed point, with the decimal count chosen so the total significant
    # figures match the request rather than the decimal count.
    exponent = math.floor(math.log10(magnitude))
    decimals = max(0, significant - 1 - exponent)
    return f"{number:.{decimals}f}"


def significant_digits_of(text: str) -> int:
    """How many significant digits a printed decimal string carries.

    Used to derive a comparison tolerance from a source's printed precision.
    """
    digits = text.strip().lstrip("+-").replace(".", "").lstrip("0")
    return len(digits.rstrip()) or 1
