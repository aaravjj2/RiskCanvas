"""
Configuration for numeric precision and determinism
"""

# All numeric outputs rounded to this many decimal places for determinism
NUMERIC_PRECISION = 8

# Tolerance for numeric comparisons
NUMERIC_TOLERANCE = 1e-10

# Fixed seed for any randomness (for deterministic testing)
FIXED_SEED = 42


def round_to_precision(value: float, precision: int = NUMERIC_PRECISION) -> float:
    """
    Round a numeric value to configured precision for determinism.
    
    Args:
        value: The value to round
        precision: Number of decimal places (default: NUMERIC_PRECISION)
    
    Returns:
        Rounded value
    """
    return round(value, precision)
