"""
Unit tests for the Simple Trading Journal application.
"""

import pytest
import pandas as pd
import os
import tempfile
from unittest.mock import patch, mock_open
from datetime import datetime, date

# Import functions to test
from app import (
    Trade,
    load_trades,
    save_trades,
    calculate_pnl,
    get_summary_stats,
    add_trade,
    TRADES_FILE
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


def test_get_summary_stats_empty():
    """Test summary stats with empty data."""
    df = pd.DataFrame()
    stats = get_summary_stats(df)
    
    assert stats['total_pnl'] == 0.0
    assert stats['win_rate'] == 0.0
    assert stats['total_trades'] == 0
    assert stats['avg_trade'] == 0.0


def test_get_summary_stats_with_data():
    """Test summary stats with sample data."""
    data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "symbol": ["AAPL", "GOOGL", "MSFT"],
        "strategy": ["Long Stock", "Short Stock", "Long Call"],
        "entry_price": [150.0, 2800.0, 300.0],
        "exit_price": [160.0, 2700.0, 0.0],
        "quantity": [10, -5, 100],
        "pnl": [100.0, 500.0, 0.0],
        "notes": ["", "", ""],
        "status": ["Closed", "Closed", "Open"]
    }
    
    df = pd.DataFrame(data)
    stats = get_summary_stats(df)
    
    assert stats['total_pnl'] == 600.0  # Only closed trades
    assert stats['win_rate'] == 1.0  # Both closed trades are winners
    assert stats['total_trades'] == 3  # All trades
    assert stats['avg_trade'] == 300.0  # Average of closed trades


def test_get_summary_stats_all_open():
    """Test summary stats when all trades are open."""
    data = {
        "date": ["2023-01-01", "2023-01-02"],
        "symbol": ["AAPL", "GOOGL"],
        "strategy": ["Long Stock", "Short Stock"],
        "entry_price": [150.0, 2800.0],
        "exit_price": [0.0, 0.0],
        "quantity": [10, -5],
        "pnl": [0.0, 0.0],
        "notes": ["", ""],
        "status": ["Open", "Open"]
    }
    
    df = pd.DataFrame(data)
    stats = get_summary_stats(df)
    
    assert stats['total_pnl'] == 0.0
    assert stats['win_rate'] == 0.0
    assert stats['total_trades'] == 2
    assert stats['avg_trade'] == 0.0


@patch("app.os.path.exists")
def test_load_trades_file_exists(mock_exists):
    """Test loading trades when file exists."""
    mock_exists.return_value = True
    
    sample_data = {
        "date": ["2023-01-01"],
        "symbol": ["AAPL"],
        "strategy": ["Long Stock"],
        "entry_price": [150.0],
        "exit_price": [160.0],
        "quantity": [10],
        "pnl": [100.0],
        "notes": [""],
        "status": ["Closed"]
    }
    
    sample_df = pd.DataFrame(sample_data)
    
    with patch("pandas.read_csv") as mock_read_csv:
        mock_read_csv.return_value = sample_df
        df = load_trades()
        
        mock_read_csv.assert_called_once_with(TRADES_FILE)
        assert not df.empty
        assert len(df) == 1


@patch("app.os.path.exists")
def test_load_trades_file_not_exists(mock_exists):
    """Test loading trades when file doesn't exist."""
    mock_exists.return_value = False
    
    df = load_trades()
    
    assert df.empty
    expected_columns = [
        "date", "symbol", "strategy", "entry_price",
        "exit_price", "quantity", "pnl", "notes", "status"
    ]
    assert list(df.columns) == expected_columns


def test_save_trades():
    """Test saving trades to CSV."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the DATA_DIR and TRADES_FILE
        with patch("app.DATA_DIR", temp_dir), \
             patch("app.TRADES_FILE", os.path.join(temp_dir, "trades.csv")):
            
            data = {
                "date": ["2023-01-01"],
                "symbol": ["AAPL"],
                "strategy": ["Long Stock"],
                "entry_price": [150.0],
                "exit_price": [160.0],
                "quantity": [10],
                "pnl": [100.0],
                "notes": [""],
                "status": ["Closed"]
            }
            
            df = pd.DataFrame(data)
            save_trades(df)
            
            # Check that file was created
            trades_file = os.path.join(temp_dir, "trades.csv")
            assert os.path.exists(trades_file)
            
            # Check content (focus on values rather than exact data types)
            loaded_df = pd.read_csv(trades_file)
            
            # Compare values
            assert loaded_df.iloc[0]["date"] == "2023-01-01"
            assert loaded_df.iloc[0]["symbol"] == "AAPL"
            assert loaded_df.iloc[0]["strategy"] == "Long Stock"
            assert loaded_df.iloc[0]["entry_price"] == 150.0
            assert loaded_df.iloc[0]["exit_price"] == 160.0
            assert loaded_df.iloc[0]["quantity"] == 10
            assert loaded_df.iloc[0]["pnl"] == 100.0
            assert loaded_df.iloc[0]["status"] == "Closed"


def test_add_trade():
    """Test adding a new trade."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the DATA_DIR and TRADES_FILE
        with patch("app.DATA_DIR", temp_dir), \
             patch("app.TRADES_FILE", os.path.join(temp_dir, "trades.csv")):
            
            # First, create an empty trades file
            empty_df = pd.DataFrame(columns=[
                "date", "symbol", "strategy", "entry_price",
                "exit_price", "quantity", "pnl", "notes", "status"
            ])
            empty_df.to_csv(os.path.join(temp_dir, "trades.csv"), index=False)
            
            # Add a new trade
            trade_data = {
                "date": "2023-01-01",
                "symbol": "AAPL",
                "strategy": "Long Stock",
                "entry_price": 150.0,
                "exit_price": 160.0,
                "quantity": 10,
                "notes": "",
                "status": "Closed"
            }
            
            add_trade(trade_data)
            
            # Check that trade was added
            df = load_trades()
            assert len(df) == 1
            assert df.iloc[0]["symbol"] == "AAPL"
            assert df.iloc[0]["pnl"] == 100.0  # (160 - 150) * 10


def test_add_trade_open_position():
    """Test adding an open trade."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the DATA_DIR and TRADES_FILE
        with patch("app.DATA_DIR", temp_dir), \
             patch("app.TRADES_FILE", os.path.join(temp_dir, "trades.csv")):
            
            # First, create an empty trades file
            empty_df = pd.DataFrame(columns=[
                "date", "symbol", "strategy", "entry_price",
                "exit_price", "quantity", "pnl", "notes", "status"
            ])
            empty_df.to_csv(os.path.join(temp_dir, "trades.csv"), index=False)
            
            # Add an open trade
            trade_data = {
                "date": "2023-01-01",
                "symbol": "AAPL",
                "strategy": "Long Stock",
                "entry_price": 150.0,
                "exit_price": 0.0,
                "quantity": 10,
                "notes": "",
                "status": "Open"
            }
            
            add_trade(trade_data)
            
            # Check that trade was added correctly
            df = load_trades()
            assert len(df) == 1
            assert df.iloc[0]["symbol"] == "AAPL"
            assert df.iloc[0]["pnl"] == 0.0  # Open trade has 0 PnL
            assert df.iloc[0]["status"] == "Open"