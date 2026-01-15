import pandas as pd
import numpy as np
import logging

def safe_round(value, decimals=2, default=None):
    """
    Safely rounds a number, handling None, pd.NA, np.nan, and strings.
    
    Args:
        value: The value to round.
        decimals (int): Number of decimal places.
        default: Return value if input is invalid/missing.
        
    Returns:
        float/int/default: Rounded value or default.
    """
    try:
        if value is None or pd.isna(value):
            return default
            
        if isinstance(value, (pd.Series, np.ndarray, list)):
            # If it's a series/list, we probably shouldn't be using this scalar function
            # But strict checking helps
            return default
            
        # Attempt conversion strictly for scalar types
        val_float = float(value)
        return round(val_float, decimals)
        
    except (TypeError, ValueError, OverflowError):
        # Fallback for truly broken types
        return default
