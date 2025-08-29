"""
Unit tests for the final polish and production ready features.
"""

import pytest
import pandas as pd
import os
import json
from unittest.mock import patch, mock_open
from app import (
    load_config,
    save_config,
    validate_trade_data,
    TradeValidationError,
    StorageError,
    display_settings_section,
    display_help_section
)


def test_load_config_default():
    """Test loading default configuration when no config file exists."""
    # Mock os.path.exists to return False
    with patch("app.os.path.exists", return_value=False):
        config = load_config()
        
        # Check that we get the default configuration
        assert isinstance(config, dict)
        assert config["currency"] == "USD"
        assert config["date_format"] == "YYYY-MM-DD"
        assert config["default_strategy"] == "Long Stock"
        assert config["theme"] == "light"
        assert config["auto_save_interval"] == 300
        assert config["backup_enabled"] == True


def test_load_config_existing():
    """Test loading existing configuration."""
    # Mock os.path.exists to return True
    with patch("app.os.path.exists", return_value=True):
        # Mock open to return sample config data
        sample_config = {
            "currency": "EUR",
            "date_format": "DD/MM/YYYY",
            "default_strategy": "Short Stock",
            "theme": "dark",
            "auto_save_interval": 600,
            "backup_enabled": False
        }
        
        with patch("app.open", mock_open(read_data=json.dumps(sample_config))):
            config = load_config()
            
            # Check that we get the loaded configuration
            assert isinstance(config, dict)
            assert config["currency"] == "EUR"
            assert config["date_format"] == "DD/MM/YYYY"
            assert config["default_strategy"] == "Short Stock"
            assert config["theme"] == "dark"
            assert config["auto_save_interval"] == 600
            assert config["backup_enabled"] == False


def test_save_config():
    """Test saving configuration."""
    # Mock os.makedirs
    with patch("app.os.makedirs"):
        # Mock open
        with patch("app.open", mock_open()) as mock_file:
            config = {
                "currency": "GBP",
                "date_format": "MM/DD/YYYY",
                "default_strategy": "Long Call",
                "theme": "light",
                "auto_save_interval": 900,
                "backup_enabled": True
            }
            
            save_config(config)
            
            # Check that open was called with correct parameters
            mock_file.assert_called_once_with(os.path.join("data", "config.json"), 'w')


def test_save_config_error():
    """Test saving configuration with error."""
    # Mock os.makedirs
    with patch("app.os.makedirs"):
        # Mock open to raise an exception
        with patch("app.open", side_effect=Exception("File error")):
            config = {
                "currency": "GBP",
                "date_format": "MM/DD/YYYY",
                "default_strategy": "Long Call",
                "theme": "light",
                "auto_save_interval": 900,
                "backup_enabled": True
            }
            
            # Check that save_config raises StorageError
            with pytest.raises(StorageError):
                save_config(config)


def test_validate_trade_data_valid():
    """Test validating valid trade data."""
    trade_data = {
        "symbol": "AAPL",
        "strategy": "Long Stock",
        "entry_price": 150.0,
        "quantity": 10
    }
    
    # This should not raise an exception
    validate_trade_data(trade_data)


def test_validate_trade_data_missing_symbol():
    """Test validating trade data with missing symbol."""
    trade_data = {
        "strategy": "Long Stock",
        "entry_price": 150.0,
        "quantity": 10
    }
    
    # This should raise TradeValidationError
    with pytest.raises(TradeValidationError, match="Symbol is required"):
        validate_trade_data(trade_data)


def test_validate_trade_data_missing_strategy():
    """Test validating trade data with missing strategy."""
    trade_data = {
        "symbol": "AAPL",
        "entry_price": 150.0,
        "quantity": 10
    }
    
    # This should raise TradeValidationError
    with pytest.raises(TradeValidationError, match="Strategy is required"):
        validate_trade_data(trade_data)


def test_validate_trade_data_invalid_entry_price():
    """Test validating trade data with invalid entry price."""
    trade_data = {
        "symbol": "AAPL",
        "strategy": "Long Stock",
        "entry_price": -50.0,
        "quantity": 10
    }
    
    # This should raise TradeValidationError
    with pytest.raises(TradeValidationError, match="Entry price must be positive"):
        validate_trade_data(trade_data)


def test_validate_trade_data_zero_quantity():
    """Test validating trade data with zero quantity."""
    trade_data = {
        "symbol": "AAPL",
        "strategy": "Long Stock",
        "entry_price": 150.0,
        "quantity": 0
    }
    
    # This should raise TradeValidationError
    with pytest.raises(TradeValidationError, match="Quantity cannot be zero"):
        validate_trade_data(trade_data)


def test_validate_trade_data_short_strategy_positive_quantity():
    """Test validating trade data with short strategy and positive quantity."""
    trade_data = {
        "symbol": "AAPL",
        "strategy": "Short Stock",
        "entry_price": 150.0,
        "quantity": 10
    }
    
    # This should raise TradeValidationError
    with pytest.raises(TradeValidationError, match="Short strategies require negative quantity"):
        validate_trade_data(trade_data)


def test_validate_trade_data_long_strategy_negative_quantity():
    """Test validating trade data with long strategy and negative quantity."""
    trade_data = {
        "symbol": "AAPL",
        "strategy": "Long Stock",
        "entry_price": 150.0,
        "quantity": -10
    }
    
    # This should raise TradeValidationError
    with pytest.raises(TradeValidationError, match="Long strategies require positive quantity"):
        validate_trade_data(trade_data)