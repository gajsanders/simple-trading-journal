"""
Unit tests for the export functionality in the Simple Trading Journal application.
"""

import pytest
import pandas as pd
import os
from unittest.mock import patch, mock_open
from app import (
    export_to_csv, 
    export_summary_report, 
    create_backup,
    get_backup_files,
    restore_from_backup
)


def test_export_to_csv():
    """Test CSV export functionality."""
    # Create sample data
    data = {
        "date": ["2023-01-01", "2023-01-02"],
        "symbol": ["AAPL", "GOOGL"],
        "strategy": ["Long Stock", "Short Stock"],
        "entry_price": [150.0, 2800.0],
        "exit_price": [160.0, 2700.0],
        "quantity": [10, -5],
        "pnl": [100.0, 500.0],
        "notes": ["Good trade", "Great trade"],
        "status": ["Closed", "Closed"]
    }
    
    df = pd.DataFrame(data)
    
    # Test basic CSV export
    csv_data = export_to_csv(df)
    assert isinstance(csv_data, bytes)
    assert len(csv_data) > 0
    
    # Test CSV export with metrics
    csv_data_with_metrics = export_to_csv(df, include_metrics=True)
    assert isinstance(csv_data_with_metrics, bytes)
    assert len(csv_data_with_metrics) > 0


def test_export_summary_report():
    """Test summary report generation."""
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
    
    # Test summary report generation
    report = export_summary_report(df)
    assert isinstance(report, str)
    assert len(report) > 0
    assert "TRADE JOURNAL SUMMARY REPORT" in report
    assert "Total P&L" in report
    assert "Win Rate" in report


def test_export_summary_report_empty():
    """Test summary report generation with empty data."""
    df = pd.DataFrame()
    
    # Test summary report generation with empty data
    report = export_summary_report(df)
    assert isinstance(report, str)
    assert len(report) > 0
    assert "No trades to report" in report


@patch("app.os.makedirs")
@patch("app.pd.DataFrame.to_csv")
@patch("app.datetime")
def test_create_backup(mock_datetime, mock_to_csv, mock_makedirs):
    """Test backup creation."""
    # Mock datetime to return a fixed value
    mock_datetime.now().strftime.return_value = "20230101_120000"
    
    # Mock load_trades to return sample data
    with patch("app.load_trades") as mock_load:
        mock_load.return_value = pd.DataFrame({
            "date": ["2023-01-01"],
            "symbol": ["AAPL"],
            "strategy": ["Long Stock"],
            "entry_price": [150.0],
            "exit_price": [160.0],
            "quantity": [10],
            "pnl": [100.0],
            "notes": [""],
            "status": ["Closed"]
        })
        
        # Test backup creation
        backup_path = create_backup()
        
        # Check that the backup path is correct
        expected_path = os.path.join("data", "backups", "trades_backup_20230101_120000.csv")
        assert backup_path == expected_path
        
        # Check that makedirs was called
        mock_makedirs.assert_called_once_with(os.path.join("data", "backups"), exist_ok=True)
        
        # Check that to_csv was called with correct path
        mock_to_csv.assert_called_once_with(expected_path, index=False)


@patch("app.os.path.exists")
@patch("app.os.listdir")
@patch("app.os.path.getmtime")
def test_get_backup_files(mock_getmtime, mock_listdir, mock_exists):
    """Test getting backup files."""
    # Mock os.path.exists to return True
    mock_exists.return_value = True
    
    # Mock os.listdir to return sample backup files
    mock_listdir.return_value = [
        "trades_backup_20230101_120000.csv",
        "trades_backup_20230102_120000.csv",
        "other_file.txt"
    ]
    
    # Mock os.path.getmtime to return different timestamps
    mock_getmtime.side_effect = [1000, 2000, 3000]
    
    # Test getting backup files
    backup_files = get_backup_files()
    
    # Check that we get the correct backup files (only CSV files with correct prefix)
    assert len(backup_files) == 2
    assert all("trades_backup_" in os.path.basename(f) for f in backup_files)
    assert all(f.endswith(".csv") for f in backup_files)
    
    # Check that files are sorted by modification time (newest first)
    assert backup_files[0].endswith("trades_backup_20230102_120000.csv")
    assert backup_files[1].endswith("trades_backup_20230101_120000.csv")


@patch("app.os.path.exists")
@patch("app.pd.read_csv")
@patch("app.save_trades")
def test_restore_from_backup(mock_save_trades, mock_read_csv, mock_exists):
    """Test restoring from backup."""
    # Mock os.path.exists to return True
    mock_exists.return_value = True
    
    # Mock pd.read_csv to return sample data
    sample_data = pd.DataFrame({
        "date": ["2023-01-01"],
        "symbol": ["AAPL"],
        "strategy": ["Long Stock"],
        "entry_price": [150.0],
        "exit_price": [160.0],
        "quantity": [10],
        "pnl": [100.0],
        "notes": [""],
        "status": ["Closed"]
    })
    mock_read_csv.return_value = sample_data
    
    # Test restoring from backup
    result = restore_from_backup("/path/to/backup.csv")
    
    # Check that the function returns True
    assert result == True
    
    # Check that pd.read_csv was called with correct path
    mock_read_csv.assert_called_once_with("/path/to/backup.csv")
    
    # Check that save_trades was called with correct data
    mock_save_trades.assert_called_once_with(sample_data)


@patch("app.os.path.exists")
def test_restore_from_backup_missing_file(mock_exists):
    """Test restoring from backup with missing file."""
    # Mock os.path.exists to return False
    mock_exists.return_value = False
    
    # Test restoring from backup with missing file
    result = restore_from_backup("/path/to/missing_backup.csv")
    
    # Check that the function returns False
    assert result == False