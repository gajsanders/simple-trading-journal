"""
Unit tests for the filtering functionality in the Simple Trading Journal application.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from app import filter_trades, create_filter_sidebar


def test_filter_trades_date_range():
    """Test filtering trades by date range."""
    # Create sample data
    data = {
        "date": ["2023-01-01", "2023-01-15", "2023-01-30"],
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
    
    # Test date range filter
    filter_config = {
        'start_date': '2023-01-10',
        'end_date': '2023-01-20'
    }
    
    filtered_df = filter_trades(df, filter_config)
    
    # Should only return the middle trade (GOOGL)
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['symbol'] == 'GOOGL'


def test_filter_trades_symbol():
    """Test filtering trades by symbol."""
    # Create sample data
    data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "symbol": ["AAPL", "GOOGL", "AAPL"],
        "strategy": ["Long Stock", "Short Stock", "Long Call"],
        "entry_price": [150.0, 2800.0, 300.0],
        "exit_price": [160.0, 2700.0, 0.0],
        "quantity": [10, -5, 100],
        "pnl": [100.0, 500.0, 0.0],
        "notes": ["", "", ""],
        "status": ["Closed", "Closed", "Open"]
    }
    
    df = pd.DataFrame(data)
    
    # Test symbol filter
    filter_config = {
        'symbols': ['AAPL']
    }
    
    filtered_df = filter_trades(df, filter_config)
    
    # Should return 2 AAPL trades
    assert len(filtered_df) == 2
    assert all(filtered_df['symbol'] == 'AAPL')


def test_filter_trades_strategy():
    """Test filtering trades by strategy."""
    # Create sample data
    data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "symbol": ["AAPL", "GOOGL", "MSFT"],
        "strategy": ["Long Stock", "Short Stock", "Long Stock"],
        "entry_price": [150.0, 2800.0, 300.0],
        "exit_price": [160.0, 2700.0, 0.0],
        "quantity": [10, -5, 100],
        "pnl": [100.0, 500.0, 0.0],
        "notes": ["", "", ""],
        "status": ["Closed", "Closed", "Open"]
    }
    
    df = pd.DataFrame(data)
    
    # Test strategy filter
    filter_config = {
        'strategies': ['Long Stock']
    }
    
    filtered_df = filter_trades(df, filter_config)
    
    # Should return 2 Long Stock trades
    assert len(filtered_df) == 2
    assert all(filtered_df['strategy'] == 'Long Stock')


def test_filter_trades_status():
    """Test filtering trades by status."""
    # Create sample data
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
    
    # Test status filter
    filter_config = {
        'statuses': ['Open']
    }
    
    filtered_df = filter_trades(df, filter_config)
    
    # Should return 1 Open trade
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['status'] == 'Open'


def test_filter_trades_pnl_range():
    """Test filtering trades by PnL range."""
    # Create sample data
    data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "symbol": ["AAPL", "GOOGL", "MSFT"],
        "strategy": ["Long Stock", "Short Stock", "Long Call"],
        "entry_price": [150.0, 2800.0, 300.0],
        "exit_price": [160.0, 2700.0, 0.0],
        "quantity": [10, -5, 100],
        "pnl": [100.0, 500.0, -200.0],
        "notes": ["", "", ""],
        "status": ["Closed", "Closed", "Open"]
    }
    
    df = pd.DataFrame(data)
    
    # Test PnL range filter
    filter_config = {
        'min_pnl': 0,
        'max_pnl': 300
    }
    
    filtered_df = filter_trades(df, filter_config)
    
    # Should return 1 trade with PnL between 0 and 300 (only AAPL with 100.0)
    assert len(filtered_df) == 1
    assert all((filtered_df['pnl'] >= 0) & (filtered_df['pnl'] <= 300))
    assert filtered_df.iloc[0]['symbol'] == 'AAPL'


def test_filter_trades_search_text():
    """Test filtering trades by search text."""
    # Create sample data
    data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "symbol": ["AAPL", "GOOGL", "MSFT"],
        "strategy": ["Long Stock", "Short Stock", "Long Call"],
        "entry_price": [150.0, 2800.0, 300.0],
        "exit_price": [160.0, 2700.0, 0.0],
        "quantity": [10, -5, 100],
        "pnl": [100.0, 500.0, 0.0],
        "notes": ["Apple Inc", "Google trade", "Microsoft trade"],
        "status": ["Closed", "Closed", "Open"]
    }
    
    df = pd.DataFrame(data)
    
    # Test search text filter (symbol)
    filter_config = {
        'search_text': 'aapl'
    }
    
    filtered_df = filter_trades(df, filter_config)
    
    # Should return 1 trade with symbol containing 'aapl'
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['symbol'] == 'AAPL'
    
    # Test search text filter (notes)
    filter_config = {
        'search_text': 'google'
    }
    
    filtered_df = filter_trades(df, filter_config)
    
    # Should return 1 trade with notes containing 'google'
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['symbol'] == 'GOOGL'


def test_filter_trades_multiple_filters():
    """Test filtering trades with multiple filters applied."""
    # Create sample data
    data = {
        "date": ["2023-01-01", "2023-01-15", "2023-01-30"],
        "symbol": ["AAPL", "GOOGL", "MSFT"],
        "strategy": ["Long Stock", "Short Stock", "Long Call"],
        "entry_price": [150.0, 2800.0, 300.0],
        "exit_price": [160.0, 2700.0, 0.0],
        "quantity": [10, -5, 100],
        "pnl": [100.0, 500.0, 0.0],
        "notes": ["Apple trade", "Google trade", "Microsoft trade"],
        "status": ["Closed", "Closed", "Open"]
    }
    
    df = pd.DataFrame(data)
    
    # Test multiple filters
    filter_config = {
        'start_date': '2023-01-10',
        'end_date': '2023-01-20',
        'symbols': ['GOOGL'],
        'min_pnl': 100,
        'search_text': 'google'
    }
    
    filtered_df = filter_trades(df, filter_config)
    
    # Should return 1 trade that matches all filters
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]['symbol'] == 'GOOGL'


def test_filter_trades_empty_dataframe():
    """Test filtering with an empty DataFrame."""
    df = pd.DataFrame()
    
    filter_config = {
        'start_date': '2023-01-01',
        'end_date': '2023-01-31'
    }
    
    filtered_df = filter_trades(df, filter_config)
    
    # Should return empty DataFrame
    assert filtered_df.empty


def test_filter_trades_no_filters():
    """Test filtering with no filters applied."""
    # Create sample data
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
    
    # Test with empty filter config
    filter_config = {}
    
    filtered_df = filter_trades(df, filter_config)
    
    # Should return all trades
    assert len(filtered_df) == len(df)
    pd.testing.assert_frame_equal(df, filtered_df)