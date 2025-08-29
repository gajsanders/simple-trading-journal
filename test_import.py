"""
Unit tests for the CSV import functionality in the Simple Trading Journal application.
"""

import pytest
import pandas as pd
from unittest.mock import Mock, patch
from app import (
    analyze_csv, 
    validate_import_data, 
    import_trades,
    calculate_pnl
)


def test_calculate_pnl():
    """Test P&L calculation."""
    # Test long position profit
    assert calculate_pnl(100, 110, 10) == 100.0
    
    # Test short position profit
    assert calculate_pnl(100, 90, -10) == 100.0
    
    # Test loss
    assert calculate_pnl(100, 90, 10) == -100.0
    
    # Test open trade (exit price = 0)
    assert calculate_pnl(100, 0, 10) == 0.0