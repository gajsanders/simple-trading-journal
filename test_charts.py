"""
Unit tests for the charting functionality in the Simple Trading Journal application.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from app import (
    get_pnl_over_time, 
    get_win_loss_distribution, 
    get_strategy_performance, 
    get_monthly_summary
)


def test_get_pnl_over_time():
    """Test P&L over time data preparation."""
    # Create sample data
    data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03"],
        "symbol": ["AAPL", "GOOGL", "MSFT"],
        "strategy": ["Long Stock", "Short Stock", "Long Call"],
        "entry_price": [150.0, 2800.0, 300.0],
        "exit_price": [160.0, 2700.0, 310.0],
        "quantity": [10, -5, 100],
        "pnl": [100.0, 500.0, 1000.0],
        "notes": ["", "", ""],
        "status": ["Closed", "Closed", "Closed"]
    }
    
    df = pd.DataFrame(data)
    
    # Test P&L over time calculation
    pnl_data = get_pnl_over_time(df)
    
    # Should have 3 rows (one for each day)
    assert len(pnl_data) == 3
    
    # Check that cumulative P&L is calculated correctly
    assert pnl_data.iloc[0]['cumulative_pnl'] == 100.0
    assert pnl_data.iloc[1]['cumulative_pnl'] == 600.0
    assert pnl_data.iloc[2]['cumulative_pnl'] == 1600.0
    
    # Check that daily P&L is correct
    assert pnl_data.iloc[0]['pnl'] == 100.0
    assert pnl_data.iloc[1]['pnl'] == 500.0
    assert pnl_data.iloc[2]['pnl'] == 1000.0


def test_get_pnl_over_time_empty():
    """Test P&L over time with empty DataFrame."""
    df = pd.DataFrame()
    
    # Test with empty DataFrame
    pnl_data = get_pnl_over_time(df)
    
    # Should return empty DataFrame with correct columns
    assert pnl_data.empty
    assert list(pnl_data.columns) == ['date', 'cumulative_pnl', 'daily_pnl']


def test_get_pnl_over_time_no_closed_trades():
    """Test P&L over time with no closed trades."""
    # Create sample data with only open trades
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
    
    # Test with no closed trades
    pnl_data = get_pnl_over_time(df)
    
    # Should return empty DataFrame
    assert pnl_data.empty


def test_get_win_loss_distribution():
    """Test win/loss distribution data preparation."""
    # Create sample data with wins, losses, and breakeven trades
    data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "symbol": ["AAPL", "GOOGL", "MSFT", "TSLA"],
        "strategy": ["Long Stock", "Short Stock", "Long Call", "Short Put"],
        "entry_price": [150.0, 2800.0, 300.0, 200.0],
        "exit_price": [160.0, 2700.0, 300.0, 190.0],
        "quantity": [10, -5, 100, -10],
        "pnl": [100.0, 500.0, 0.0, -100.0],
        "notes": ["", "", "", ""],
        "status": ["Closed", "Closed", "Closed", "Closed"]
    }
    
    df = pd.DataFrame(data)
    
    # Test win/loss distribution calculation
    win_loss_data = get_win_loss_distribution(df)
    
    # Should have 3 categories
    assert len(win_loss_data) == 3
    
    # Check counts
    wins = win_loss_data[win_loss_data['category'] == 'Wins']['count'].iloc[0]
    losses = win_loss_data[win_loss_data['category'] == 'Losses']['count'].iloc[0]
    breakeven = win_loss_data[win_loss_data['category'] == 'Breakeven']['count'].iloc[0]
    
    assert wins == 2  # AAPL and GOOGL
    assert losses == 1  # TSLA
    assert breakeven == 1  # MSFT


def test_get_win_loss_distribution_empty():
    """Test win/loss distribution with empty DataFrame."""
    df = pd.DataFrame()
    
    # Test with empty DataFrame
    win_loss_data = get_win_loss_distribution(df)
    
    # Should return empty DataFrame with correct columns
    assert win_loss_data.empty
    assert list(win_loss_data.columns) == ['category', 'count']


def test_get_strategy_performance():
    """Test strategy performance data preparation."""
    # Create sample data with different strategies
    data = {
        "date": ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "symbol": ["AAPL", "GOOGL", "MSFT", "TSLA"],
        "strategy": ["Long Stock", "Long Stock", "Short Stock", "Long Call"],
        "entry_price": [150.0, 2800.0, 300.0, 200.0],
        "exit_price": [160.0, 2700.0, 290.0, 210.0],
        "quantity": [10, -5, -10, 100],
        "pnl": [100.0, 500.0, -100.0, 1000.0],
        "notes": ["", "", "", ""],
        "status": ["Closed", "Closed", "Closed", "Closed"]
    }
    
    df = pd.DataFrame(data)
    
    # Test strategy performance calculation
    strategy_data = get_strategy_performance(df)
    
    # Should have 3 strategies
    assert len(strategy_data) == 3
    
    # Check Long Stock performance (AAPL + GOOGL)
    long_stock = strategy_data[strategy_data['strategy'] == 'Long Stock']
    assert len(long_stock) == 1
    assert long_stock.iloc[0]['total_pnl'] == 600.0  # 100 + 500
    
    # Check Short Stock performance
    short_stock = strategy_data[strategy_data['strategy'] == 'Short Stock']
    assert len(short_stock) == 1
    assert short_stock.iloc[0]['total_pnl'] == -100.0
    
    # Check Long Call performance
    long_call = strategy_data[strategy_data['strategy'] == 'Long Call']
    assert len(long_call) == 1
    assert long_call.iloc[0]['total_pnl'] == 1000.0


def test_get_strategy_performance_empty():
    """Test strategy performance with empty DataFrame."""
    df = pd.DataFrame()
    
    # Test with empty DataFrame
    strategy_data = get_strategy_performance(df)
    
    # Should return empty DataFrame with correct columns
    assert strategy_data.empty
    assert list(strategy_data.columns) == ['strategy', 'total_pnl', 'avg_pnl']


def test_get_monthly_summary():
    """Test monthly summary data preparation."""
    # Create sample data across different months
    data = {
        "date": ["2023-01-15", "2023-01-20", "2023-02-05", "2023-02-10"],
        "symbol": ["AAPL", "GOOGL", "MSFT", "TSLA"],
        "strategy": ["Long Stock", "Long Stock", "Short Stock", "Long Call"],
        "entry_price": [150.0, 2800.0, 300.0, 200.0],
        "exit_price": [160.0, 2700.0, 290.0, 210.0],
        "quantity": [10, -5, -10, 100],
        "pnl": [100.0, 500.0, -100.0, 1000.0],
        "notes": ["", "", "", ""],
        "status": ["Closed", "Closed", "Closed", "Closed"]
    }
    
    df = pd.DataFrame(data)
    
    # Test monthly summary calculation
    monthly_data = get_monthly_summary(df)
    
    # Should have 2 months
    assert len(monthly_data) == 2
    
    # Check January performance (AAPL + GOOGL)
    january = monthly_data[monthly_data['month'] == '2023-01']
    assert len(january) == 1
    assert january.iloc[0]['pnl'] == 600.0  # 100 + 500
    
    # Check February performance (MSFT + TSLA)
    february = monthly_data[monthly_data['month'] == '2023-02']
    assert len(february) == 1
    assert february.iloc[0]['pnl'] == 900.0  # -100 + 1000


def test_get_monthly_summary_empty():
    """Test monthly summary with empty DataFrame."""
    df = pd.DataFrame()
    
    # Test with empty DataFrame
    monthly_data = get_monthly_summary(df)
    
    # Should return empty DataFrame with correct columns
    assert monthly_data.empty
    assert list(monthly_data.columns) == ['month', 'pnl']