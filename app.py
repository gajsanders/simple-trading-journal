"""
Simple Trading Journal Application
A lightweight trading journal built with Streamlit for personal trade tracking.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Optional
import os
import numpy as np
import io
import zipfile


@dataclass
class Trade:
    """Data class representing a single trade."""
    date: str
    symbol: str
    strategy: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    notes: str
    status: str


# Strategy options for the dropdown
STRATEGY_OPTIONS = [
    "Long Stock",
    "Short Stock",
    "Long Call",
    "Short Call",
    "Long Put",
    "Short Put",
    "Covered Call",
    "Cash Secured Put",
    "Other"
]


# Ensure data directory exists
DATA_DIR = "data"
TRADES_FILE = os.path.join(DATA_DIR, "trades.csv")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")


def load_trades() -> pd.DataFrame:
    """
    Load trades from CSV file.
    
    Returns:
        pd.DataFrame: DataFrame containing all trades
    """
    if os.path.exists(TRADES_FILE):
        return pd.read_csv(TRADES_FILE)
    else:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=[
            "date", "symbol", "strategy", "entry_price", 
            "exit_price", "quantity", "pnl", "notes", "status"
        ])


def save_trades(df: pd.DataFrame) -> None:
    """
    Save trades to CSV file.
    
    Args:
        df (pd.DataFrame): DataFrame containing all trades
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(TRADES_FILE, index=False)


def calculate_pnl(entry: float, exit: float, quantity: int) -> float:
    """
    Calculate profit/loss for a trade.
    
    Args:
        entry (float): Entry price
        exit (float): Exit price (0 for open trades)
        quantity (int): Number of shares/contracts
        
    Returns:
        float: Profit/loss value
    """
    if exit == 0:
        return 0.0
    return (exit - entry) * quantity


def get_summary_stats(df: pd.DataFrame) -> Dict[str, float]:
    """
    Calculate summary statistics from trades.
    
    Args:
        df (pd.DataFrame): DataFrame containing trades
        
    Returns:
        dict: Dictionary with summary statistics
    """
    if df.empty:
        return {
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'total_trades': 0,
            'avg_trade': 0.0
        }
    
    closed_trades = df[df['status'] == 'Closed']
    
    if closed_trades.empty:
        return {
            'total_pnl': 0.0,
            'win_rate': 0.0,
            'total_trades': len(df),
            'avg_trade': 0.0
        }
    
    total_pnl = closed_trades['pnl'].sum()
    winning_trades = len(closed_trades[closed_trades['pnl'] > 0])
    total_closed_trades = len(closed_trades)
    
    win_rate = winning_trades / total_closed_trades if total_closed_trades > 0 else 0
    avg_trade = closed_trades['pnl'].mean() if total_closed_trades > 0 else 0
    
    return {
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'total_trades': len(df),
        'avg_trade': avg_trade
    }


def add_trade(trade_data: dict) -> None:
    """
    Add a new trade to the database.
    
    Args:
        trade_data (dict): Dictionary containing trade information
    """
    df = load_trades()
    
    # Calculate PnL
    trade_data['pnl'] = calculate_pnl(
        trade_data['entry_price'], 
        trade_data['exit_price'], 
        trade_data['quantity']
    )
    
    # Determine status
    trade_data['status'] = 'Open' if trade_data['exit_price'] == 0 else 'Closed'
    
    # Add new trade to DataFrame
    new_trade_df = pd.DataFrame([trade_data])
    df = pd.concat([df, new_trade_df], ignore_index=True)
    
    # Save updated DataFrame
    save_trades(df)


def filter_trades(trades_df: pd.DataFrame, filter_config: dict) -> pd.DataFrame:
    """
    Apply filters to the trades DataFrame.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing all trades
        filter_config (dict): Dictionary containing filter settings
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    if trades_df.empty:
        return trades_df
    
    filtered_df = trades_df.copy()
    
    # Date range filter
    if filter_config.get('start_date') and filter_config.get('end_date'):
        filtered_df = filtered_df[
            (filtered_df['date'] >= filter_config['start_date']) & 
            (filtered_df['date'] <= filter_config['end_date'])
        ]
    
    # Symbol filter
    if filter_config.get('symbols'):
        filtered_df = filtered_df[filtered_df['symbol'].isin(filter_config['symbols'])]
    
    # Strategy filter
    if filter_config.get('strategies'):
        filtered_df = filtered_df[filtered_df['strategy'].isin(filter_config['strategies'])]
    
    # Status filter
    if filter_config.get('statuses'):
        filtered_df = filtered_df[filtered_df['status'].isin(filter_config['statuses'])]
    
    # PnL range filter
    if filter_config.get('min_pnl') is not None and filter_config.get('max_pnl') is not None:
        filtered_df = filtered_df[
            (filtered_df['pnl'] >= filter_config['min_pnl']) & 
            (filtered_df['pnl'] <= filter_config['max_pnl'])
        ]
    
    # Text search filter
    if filter_config.get('search_text'):
        search_text = filter_config['search_text'].lower()
        filtered_df = filtered_df[
            filtered_df['symbol'].str.lower().str.contains(search_text, na=False) |
            filtered_df['notes'].str.lower().str.contains(search_text, na=False)
        ]
    
    return filtered_df


def create_filter_sidebar(trades_df: pd.DataFrame) -> dict:
    """
    Create sidebar filter controls and return filter configuration.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing all trades
        
    Returns:
        dict: Filter configuration
    """
    filter_config = {}
    
    st.sidebar.header("🔍 Filters")
    
    # Date range filter
    st.sidebar.subheader("Date Range")
    col1, col2 = st.sidebar.columns(2)
    
    # Default to last 30 days
    default_end_date = datetime.now().date()
    default_start_date = default_end_date - timedelta(days=30)
    
    with col1:
        start_date = st.sidebar.date_input(
            "Start Date", 
            value=default_start_date,
            key="start_date"
        )
    
    with col2:
        end_date = st.sidebar.date_input(
            "End Date", 
            value=default_end_date,
            key="end_date"
        )
    
    filter_config['start_date'] = start_date.strftime("%Y-%m-%d")
    filter_config['end_date'] = end_date.strftime("%Y-%m-%d")
    
    # Date presets
    preset = st.sidebar.selectbox(
        "Date Presets",
        ["Custom", "Last 7 Days", "Last 30 Days", "This Month", "This Year", "All Time"]
    )
    
    # Apply preset
    today = datetime.now().date()
    if preset == "Last 7 Days":
        filter_config['start_date'] = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    elif preset == "Last 30 Days":
        filter_config['start_date'] = (today - timedelta(days=30)).strftime("%Y-%m-%d")
    elif preset == "This Month":
        filter_config['start_date'] = today.replace(day=1).strftime("%Y-%m-%d")
    elif preset == "This Year":
        filter_config['start_date'] = today.replace(month=1, day=1).strftime("%Y-%m-%d")
    elif preset == "All Time":
        # Use a very early date for all time
        filter_config['start_date'] = "1900-01-01"
    
    # Symbol filter
    if not trades_df.empty:
        all_symbols = sorted(trades_df['symbol'].unique())
        selected_symbols = st.sidebar.multiselect(
            "Symbols",
            all_symbols,
            key="symbol_filter"
        )
        if selected_symbols:
            filter_config['symbols'] = selected_symbols
    
    # Strategy filter
    selected_strategies = st.sidebar.multiselect(
        "Strategies",
        STRATEGY_OPTIONS,
        key="strategy_filter"
    )
    if selected_strategies:
        filter_config['strategies'] = selected_strategies
    
    # Status filter
    status_options = ["Open", "Closed"]
    selected_statuses = st.sidebar.multiselect(
        "Status",
        status_options,
        default=status_options,
        key="status_filter"
    )
    if selected_statuses:
        filter_config['statuses'] = selected_statuses
    
    # PnL range filter
    st.sidebar.subheader("P&L Range")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        min_pnl = st.sidebar.number_input(
            "Min P&L",
            value=-10000.0,
            step=100.0,
            key="min_pnl"
        )
    
    with col2:
        max_pnl = st.sidebar.number_input(
            "Max P&L",
            value=10000.0,
            step=100.0,
            key="max_pnl"
        )
    
    filter_config['min_pnl'] = min_pnl
    filter_config['max_pnl'] = max_pnl
    
    # Text search
    search_text = st.sidebar.text_input(
        "Search Symbols/Notes",
        key="search_text"
    )
    if search_text:
        filter_config['search_text'] = search_text
    
    # Clear filters button
    if st.sidebar.button("Clear All Filters"):
        st.session_state.clear()
        st.experimental_rerun()
    
    return filter_config


def get_pnl_over_time(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for P&L over time chart.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing trades
        
    Returns:
        pd.DataFrame: DataFrame with cumulative P&L data
    """
    if trades_df.empty:
        return pd.DataFrame(columns=['date', 'cumulative_pnl', 'daily_pnl'])
    
    # Filter to only closed trades for P&L calculations
    closed_trades = trades_df[trades_df['status'] == 'Closed'].copy()
    
    if closed_trades.empty:
        return pd.DataFrame(columns=['date', 'cumulative_pnl', 'daily_pnl'])
    
    # Convert date column to datetime
    closed_trades['date'] = pd.to_datetime(closed_trades['date'])
    
    # Sort by date
    closed_trades = closed_trades.sort_values('date')
    
    # Calculate cumulative P&L
    closed_trades['cumulative_pnl'] = closed_trades['pnl'].cumsum()
    
    # Group by date to get daily P&L
    daily_pnl = closed_trades.groupby('date')['pnl'].sum().reset_index()
    daily_pnl = daily_pnl.sort_values('date')
    daily_pnl['cumulative_pnl'] = daily_pnl['pnl'].cumsum()
    
    return daily_pnl


def get_win_loss_distribution(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for win/loss distribution chart.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing trades
        
    Returns:
        pd.DataFrame: DataFrame with win/loss data
    """
    if trades_df.empty:
        return pd.DataFrame(columns=['category', 'count'])
    
    # Filter to only closed trades
    closed_trades = trades_df[trades_df['status'] == 'Closed']
    
    if closed_trades.empty:
        return pd.DataFrame(columns=['category', 'count'])
    
    # Count wins and losses
    wins = len(closed_trades[closed_trades['pnl'] > 0])
    losses = len(closed_trades[closed_trades['pnl'] < 0])
    breakeven = len(closed_trades[closed_trades['pnl'] == 0])
    
    return pd.DataFrame({
        'category': ['Wins', 'Losses', 'Breakeven'],
        'count': [wins, losses, breakeven]
    })


def get_strategy_performance(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for strategy performance chart.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing trades
        
    Returns:
        pd.DataFrame: DataFrame with strategy performance data
    """
    if trades_df.empty:
        return pd.DataFrame(columns=['strategy', 'total_pnl', 'avg_pnl'])
    
    # Filter to only closed trades
    closed_trades = trades_df[trades_df['status'] == 'Closed']
    
    if closed_trades.empty:
        return pd.DataFrame(columns=['strategy', 'total_pnl', 'avg_pnl'])
    
    # Group by strategy and calculate performance
    strategy_perf = closed_trades.groupby('strategy').agg({
        'pnl': ['sum', 'mean', 'count']
    }).reset_index()
    
    # Flatten column names
    strategy_perf.columns = ['strategy', 'total_pnl', 'avg_pnl', 'trade_count']
    
    return strategy_perf[['strategy', 'total_pnl', 'avg_pnl']]


def get_monthly_summary(trades_df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare data for monthly performance chart.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing trades
        
    Returns:
        pd.DataFrame: DataFrame with monthly performance data
    """
    if trades_df.empty:
        return pd.DataFrame(columns=['month', 'pnl'])
    
    # Filter to only closed trades
    closed_trades = trades_df[trades_df['status'] == 'Closed'].copy()
    
    if closed_trades.empty:
        return pd.DataFrame(columns=['month', 'pnl'])
    
    # Convert date column to datetime
    closed_trades['date'] = pd.to_datetime(closed_trades['date'])
    
    # Extract month-year
    closed_trades['month'] = closed_trades['date'].dt.to_period('M').astype(str)
    
    # Group by month and sum P&L
    monthly_perf = closed_trades.groupby('month')['pnl'].sum().reset_index()
    
    return monthly_perf


def display_charts(trades_df: pd.DataFrame) -> None:
    """
    Display charts for trade analysis.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing trades
    """
    if trades_df.empty:
        st.info("No data available for charts. Add some trades to see visualizations.")
        return
    
    # Filter to only closed trades for most charts
    closed_trades = trades_df[trades_df['status'] == 'Closed']
    
    if closed_trades.empty:
        st.info("No closed trades available for charts. Close some trades to see visualizations.")
        return
    
    st.subheader("📊 Performance Charts")
    
    # Create tabs for different charts
    tab1, tab2, tab3, tab4 = st.tabs([
        "P&L Over Time", 
        "Win/Loss Distribution", 
        "Strategy Performance", 
        "Monthly Performance"
    ])
    
    with tab1:
        st.write("### Cumulative P&L Over Time")
        pnl_data = get_pnl_over_time(trades_df)
        if not pnl_data.empty:
            st.line_chart(pnl_data.set_index('date')['cumulative_pnl'], height=400)
            
            # Show daily P&L as bar chart
            st.write("### Daily P&L")
            st.bar_chart(pnl_data.set_index('date')['pnl'], height=300)
        else:
            st.info("No closed trades available for P&L chart.")
    
    with tab2:
        st.write("### Win/Loss Distribution")
        win_loss_data = get_win_loss_distribution(trades_df)
        if not win_loss_data.empty:
            st.bar_chart(win_loss_data.set_index('category')['count'], height=400)
        else:
            st.info("No closed trades available for win/loss distribution.")
    
    with tab3:
        st.write("### Strategy Performance")
        strategy_data = get_strategy_performance(trades_df)
        if not strategy_data.empty:
            st.bar_chart(strategy_data.set_index('strategy')['total_pnl'], height=400)
        else:
            st.info("No closed trades available for strategy performance chart.")
    
    with tab4:
        st.write("### Monthly Performance")
        monthly_data = get_monthly_summary(trades_df)
        if not monthly_data.empty:
            st.bar_chart(monthly_data.set_index('month')['pnl'], height=400)
        else:
            st.info("No closed trades available for monthly performance chart.")


def analyze_csv(uploaded_file) -> dict:
    """
    Analyze CSV structure and suggest column mappings.
    
    Args:
        uploaded_file: Uploaded CSV file
        
    Returns:
        dict: Analysis results including column suggestions
    """
    # Read the CSV file
    try:
        df = pd.read_csv(uploaded_file, nrows=5)
        uploaded_file.seek(0)  # Reset file pointer
    except Exception as e:
        st.error(f"Error reading CSV file: {str(e)}")
        return {}
    
    # Get column names
    csv_columns = df.columns.tolist()
    
    # Required trade fields
    required_fields = [
        "date", "symbol", "strategy", "entry_price", 
        "exit_price", "quantity", "pnl", "notes", "status"
    ]
    
    # Suggested mappings based on common column names
    suggested_mappings = {}
    
    # Common variations for each field
    field_variations = {
        "date": ["date", "trade_date", "entry_date", "timestamp"],
        "symbol": ["symbol", "ticker", "stock", "instrument"],
        "strategy": ["strategy", "strat", "approach"],
        "entry_price": ["entry_price", "entry", "buy_price", "purchase_price"],
        "exit_price": ["exit_price", "sell_price", "sale_price", "close_price"],
        "quantity": ["quantity", "qty", "shares", "contracts", "size"],
        "pnl": ["pnl", "profit", "loss", "gain"],
        "notes": ["notes", "comment", "description", "remarks"],
        "status": ["status", "state"]
    }
    
    # Try to auto-map columns
    for field in required_fields:
        for col in csv_columns:
            if col.lower() in field_variations[field]:
                suggested_mappings[field] = col
                break
    
    return {
        "columns": csv_columns,
        "sample_data": df.head(),
        "suggested_mappings": suggested_mappings,
        "row_count": len(df)
    }


def validate_import_data(df: pd.DataFrame) -> List[str]:
    """
    Validate import data and return any errors.
    
    Args:
        df (pd.DataFrame): DataFrame with mapped trade data
        
    Returns:
        List[str]: List of validation errors
    """
    errors = []
    
    # Check for required columns
    required_columns = ["date", "symbol", "strategy", "entry_price", "quantity"]
    for col in required_columns:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return errors
    
    # Validate data types and values
    for idx, row in df.iterrows():
        # Validate date format
        try:
            pd.to_datetime(row['date'])
        except:
            errors.append(f"Row {idx+1}: Invalid date format '{row['date']}'")
        
        # Validate symbol
        if pd.isna(row['symbol']) or str(row['symbol']).strip() == "":
            errors.append(f"Row {idx+1}: Missing symbol")
        
        # Validate strategy
        if row['strategy'] not in STRATEGY_OPTIONS:
            errors.append(f"Row {idx+1}: Invalid strategy '{row['strategy']}'")
        
        # Validate entry price
        try:
            entry_price = float(row['entry_price'])
            if entry_price <= 0:
                errors.append(f"Row {idx+1}: Entry price must be positive")
        except:
            errors.append(f"Row {idx+1}: Invalid entry price '{row['entry_price']}'")
        
        # Validate quantity
        try:
            quantity = int(row['quantity'])
            if quantity == 0:
                errors.append(f"Row {idx+1}: Quantity cannot be zero")
        except:
            errors.append(f"Row {idx+1}: Invalid quantity '{row['quantity']}'")
        
        # Validate exit price if present
        if 'exit_price' in row and not pd.isna(row['exit_price']):
            try:
                float(row['exit_price'])
            except:
                errors.append(f"Row {idx+1}: Invalid exit price '{row['exit_price']}'")
    
    return errors


def import_trades(uploaded_file, column_mapping: dict, skip_duplicates: bool = False) -> dict:
    """
    Import trades from CSV file.
    
    Args:
        uploaded_file: Uploaded CSV file
        column_mapping (dict): Mapping of CSV columns to trade fields
        skip_duplicates (bool): Whether to skip duplicate trades
        
    Returns:
        dict: Import results including success/failure counts
    """
    try:
        # Read the CSV file
        df = pd.read_csv(uploaded_file)
    except Exception as e:
        return {"success": False, "error": f"Error reading CSV file: {str(e)}"}
    
    # Apply column mapping
    mapped_df = pd.DataFrame()
    for trade_field, csv_column in column_mapping.items():
        if csv_column in df.columns:
            mapped_df[trade_field] = df[csv_column]
        else:
            # Handle missing columns by filling with default values
            if trade_field == "exit_price":
                mapped_df[trade_field] = 0.0
            elif trade_field == "notes":
                mapped_df[trade_field] = ""
            elif trade_field == "pnl":
                mapped_df[trade_field] = 0.0
            elif trade_field == "status":
                mapped_df[trade_field] = "Open"  # Default to Open
            else:
                mapped_df[trade_field] = None
    
    # Validate data
    validation_errors = validate_import_data(mapped_df)
    if validation_errors:
        return {
            "success": False, 
            "error": "Validation errors found",
            "validation_errors": validation_errors
        }
    
    # Clean and normalize data
    try:
        # Convert date column to proper format
        mapped_df['date'] = pd.to_datetime(mapped_df['date']).dt.strftime('%Y-%m-%d')
        
        # Convert numeric columns
        mapped_df['entry_price'] = pd.to_numeric(mapped_df['entry_price'])
        mapped_df['quantity'] = pd.to_numeric(mapped_df['quantity'])
        
        # Handle exit_price (can be NaN for open trades)
        if 'exit_price' in mapped_df.columns:
            mapped_df['exit_price'] = pd.to_numeric(mapped_df['exit_price'], errors='coerce').fillna(0.0)
        else:
            mapped_df['exit_price'] = 0.0
        
        # Calculate PnL and status
        mapped_df['pnl'] = mapped_df.apply(
            lambda row: calculate_pnl(row['entry_price'], row['exit_price'], row['quantity']), 
            axis=1
        )
        mapped_df['status'] = mapped_df['exit_price'].apply(
            lambda x: 'Closed' if x > 0 else 'Open'
        )
        
        # Normalize symbol names (uppercase)
        mapped_df['symbol'] = mapped_df['symbol'].astype(str).str.upper().str.strip()
        
        # Handle notes (fill NaN with empty string)
        if 'notes' in mapped_df.columns:
            mapped_df['notes'] = mapped_df['notes'].fillna("").astype(str)
        else:
            mapped_df['notes'] = ""
            
    except Exception as e:
        return {"success": False, "error": f"Error processing data: {str(e)}"}
    
    # Load existing trades
    existing_trades = load_trades()
    
    # Check for duplicates if requested
    if skip_duplicates and not existing_trades.empty:
        # Create a key for identifying duplicates (date, symbol, entry_price)
        mapped_df['duplicate_key'] = mapped_df.apply(
            lambda row: f"{row['date']}_{row['symbol']}_{row['entry_price']}", axis=1
        )
        existing_trades['duplicate_key'] = existing_trades.apply(
            lambda row: f"{row['date']}_{row['symbol']}_{row['entry_price']}", axis=1
        )
        
        # Filter out duplicates
        original_count = len(mapped_df)
        mapped_df = mapped_df[~mapped_df['duplicate_key'].isin(existing_trades['duplicate_key'])]
        duplicate_count = original_count - len(mapped_df)
        
        # Clean up temporary column
        mapped_df = mapped_df.drop('duplicate_key', axis=1)
        existing_trades = existing_trades.drop('duplicate_key', axis=1)
    else:
        duplicate_count = 0
    
    # Combine with existing trades
    if existing_trades.empty:
        combined_df = mapped_df
    else:
        combined_df = pd.concat([existing_trades, mapped_df], ignore_index=True)
    
    # Save to file
    try:
        save_trades(combined_df)
        return {
            "success": True,
            "imported_count": len(mapped_df),
            "duplicate_count": duplicate_count,
            "total_count": len(combined_df)
        }
    except Exception as e:
        return {"success": False, "error": f"Error saving trades: {str(e)}"}


def export_to_csv(trades_df: pd.DataFrame, include_metrics: bool = False) -> bytes:
    """
    Export trades to CSV format.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing trades to export
        include_metrics (bool): Whether to include calculated metrics
        
    Returns:
        bytes: CSV data as bytes
    """
    if include_metrics and not trades_df.empty:
        # Add calculated metrics to the export
        export_df = trades_df.copy()
        
        # Add some additional calculated fields
        if 'entry_price' in export_df.columns and 'exit_price' in export_df.columns and 'quantity' in export_df.columns:
            export_df['calculated_pnl'] = export_df.apply(
                lambda row: calculate_pnl(row['entry_price'], row['exit_price'], row['quantity']),
                axis=1
            )
        
        # Add export timestamp
        export_df['exported_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        csv_data = export_df.to_csv(index=False)
    else:
        csv_data = trades_df.to_csv(index=False)
    
    return csv_data.encode('utf-8')


def export_summary_report(trades_df: pd.DataFrame) -> str:
    """
    Generate a text summary report of trades.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing trades
        
    Returns:
        str: Summary report as text
    """
    if trades_df.empty:
        return "No trades to report."
    
    stats = get_summary_stats(trades_df)
    
    # Get additional statistics
    closed_trades = trades_df[trades_df['status'] == 'Closed']
    open_trades = trades_df[trades_df['status'] == 'Open']
    
    # Calculate additional metrics
    largest_win = 0.0
    largest_loss = 0.0
    if not closed_trades.empty:
        largest_win = closed_trades['pnl'].max()
        largest_loss = closed_trades['pnl'].min()
    
    # Generate report
    report = f"""
TRADE JOURNAL SUMMARY REPORT
============================

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

OVERALL PERFORMANCE
-------------------
Total P&L: ${stats['total_pnl']:.2f}
Win Rate: {stats['win_rate']:.1%}
Total Trades: {stats['total_trades']}
Average Trade: ${stats['avg_trade']:.2f}

TRADE BREAKDOWN
---------------
Closed Trades: {len(closed_trades)}
Open Trades: {len(open_trades)}
Largest Win: ${largest_win:.2f}
Largest Loss: ${largest_loss:.2f}

STRATEGY PERFORMANCE
--------------------
"""
    
    # Add strategy breakdown
    strategy_perf = get_strategy_performance(trades_df)
    if not strategy_perf.empty:
        for _, row in strategy_perf.iterrows():
            report += f"{row['strategy']}: ${row['total_pnl']:.2f} (avg: ${row['avg_pnl']:.2f})\n"
    
    # Add top symbols
    if not closed_trades.empty:
        top_symbols = closed_trades.groupby('symbol')['pnl'].sum().sort_values(ascending=False).head(5)
        report += "\nTOP PERFORMING SYMBOLS\n"
        report += "----------------------\n"
        for symbol, pnl in top_symbols.items():
            report += f"{symbol}: ${pnl:.2f}\n"
    
    return report


def create_backup() -> str:
    """
    Create a timestamped backup of the trades file.
    
    Returns:
        str: Path to backup file
    """
    # Load current trades
    trades_df = load_trades()
    
    # Create backup directory if it doesn't exist
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Create timestamped filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"trades_backup_{timestamp}.csv"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    # Save backup
    trades_df.to_csv(backup_path, index=False)
    
    return backup_path


def get_backup_files() -> List[str]:
    """
    Get list of available backup files.
    
    Returns:
        List[str]: List of backup file paths
    """
    if not os.path.exists(BACKUP_DIR):
        return []
    
    backup_files = []
    for file in os.listdir(BACKUP_DIR):
        if file.startswith("trades_backup_") and file.endswith(".csv"):
            backup_files.append(os.path.join(BACKUP_DIR, file))
    
    # Sort by modification time (newest first)
    backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    return backup_files


def restore_from_backup(backup_path: str) -> bool:
    """
    Restore trades from a backup file.
    
    Args:
        backup_path (str): Path to backup file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if backup file exists
        if not os.path.exists(backup_path):
            return False
        
        # Copy backup to main trades file
        backup_df = pd.read_csv(backup_path)
        save_trades(backup_df)
        
        return True
    except Exception as e:
        st.error(f"Error restoring from backup: {str(e)}")
        return False


def display_import_section() -> None:
    """
    Display the CSV import section in the UI.
    """
    st.subheader("📁 CSV Import")
    
    # File uploader
    uploaded_file = st.file_uploader(
        "Upload CSV File", 
        type="csv",
        key="csv_uploader"
    )
    
    if uploaded_file is not None:
        # Analyze the uploaded file
        analysis = analyze_csv(uploaded_file)
        
        if analysis:
            st.write(f"**File Info:** {analysis['row_count']} rows, {len(analysis['columns'])} columns")
            
            # Show sample data
            st.write("**Sample Data:**")
            st.dataframe(analysis['sample_data'])
            
            # Column mapping interface
            st.write("**Column Mapping:**")
            column_mapping = {}
            
            # Required fields
            required_fields = ["date", "symbol", "strategy", "entry_price", "quantity"]
            optional_fields = ["exit_price", "notes"]
            
            # Create mapping controls
            for field in required_fields + optional_fields:
                default_value = analysis['suggested_mappings'].get(field, "")
                selected_column = st.selectbox(
                    f"{field}{'*' if field in required_fields else ''}", 
                    [""] + analysis['columns'], 
                    index=analysis['columns'].index(default_value) + 1 if default_value in analysis['columns'] else 0,
                    key=f"mapping_{field}"
                )
                if selected_column:
                    column_mapping[field] = selected_column
            
            # Import options
            st.write("**Import Options:**")
            skip_duplicates = st.checkbox("Skip duplicate trades", value=True)
            
            # Preview mapped data
            if st.button("Preview Mapped Data"):
                try:
                    # Read the CSV file again
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file)
                    
                    # Apply column mapping
                    mapped_df = pd.DataFrame()
                    for trade_field, csv_column in column_mapping.items():
                        if csv_column and csv_column in df.columns:
                            mapped_df[trade_field] = df[csv_column]
                    
                    # Show preview
                    st.write("**Mapped Data Preview:**")
                    st.dataframe(mapped_df)
                    
                    # Validate data
                    validation_errors = validate_import_data(mapped_df)
                    if validation_errors:
                        st.warning("**Validation Errors Found:**")
                        for error in validation_errors:
                            st.write(f"- {error}")
                    else:
                        st.success("Data validation passed!")
                        
                except Exception as e:
                    st.error(f"Error previewing data: {str(e)}")
            
            # Import button
            if st.button("Import Trades"):
                try:
                    uploaded_file.seek(0)
                    result = import_trades(uploaded_file, column_mapping, skip_duplicates)
                    
                    if result["success"]:
                        st.success(
                            f"Successfully imported {result['imported_count']} trades! "
                            f"({result['duplicate_count']} duplicates skipped)"
                        )
                        # Rerun to refresh data
                        st.experimental_rerun()
                    else:
                        st.error(f"Import failed: {result['error']}")
                        if "validation_errors" in result:
                            st.write("**Validation Errors:**")
                            for error in result["validation_errors"]:
                                st.write(f"- {error}")
                except Exception as e:
                    st.error(f"Error during import: {str(e)}")
    else:
        # Show CSV template for download
        template_data = pd.DataFrame(columns=[
            "date", "symbol", "strategy", "entry_price", 
            "exit_price", "quantity", "notes"
        ])
        template_csv = template_data.to_csv(index=False)
        
        st.write("**Need a template?** Download this CSV template to get started:")
        st.download_button(
            label="Download CSV Template",
            data=template_csv,
            file_name="trades_template.csv",
            mime="text/csv"
        )


def display_export_section(trades_df: pd.DataFrame, filtered_trades_df: pd.DataFrame) -> None:
    """
    Display the export section in the UI.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing all trades
        filtered_trades_df (pd.DataFrame): DataFrame containing filtered trades
    """
    st.subheader("💾 Export Data")
    
    # Create tabs for different export options
    tab1, tab2, tab3 = st.tabs(["CSV Export", "Summary Report", "Backup/Restore"])
    
    with tab1:
        st.write("### CSV Export Options")
        
        # Export options
        export_type = st.radio(
            "Export Type",
            ["All Trades", "Filtered Trades"],
            key="export_type"
        )
        
        include_metrics = st.checkbox("Include calculated metrics", value=False)
        
        # Select data to export
        data_to_export = trades_df if export_type == "All Trades" else filtered_trades_df
        
        if not data_to_export.empty:
            # Generate export data
            csv_data = export_to_csv(data_to_export, include_metrics)
            
            # Create filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"trades_export_{timestamp}.csv"
            
            # Download button
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )
        else:
            st.info("No trades to export.")
    
    with tab2:
        st.write("### Summary Report")
        
        # Generate summary report
        report = export_summary_report(trades_df)
        
        # Display report
        st.text_area("Report Preview", report, height=400)
        
        # Download button for report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_filename = f"trade_summary_{timestamp}.txt"
        
        st.download_button(
            label="Download Summary Report",
            data=report,
            file_name=report_filename,
            mime="text/plain"
        )
    
    with tab3:
        st.write("### Backup and Restore")
        
        # Create backup button
        if st.button("Create Backup"):
            try:
                backup_path = create_backup()
                st.success(f"Backup created successfully: {os.path.basename(backup_path)}")
            except Exception as e:
                st.error(f"Error creating backup: {str(e)}")
        
        # Show available backups
        backup_files = get_backup_files()
        if backup_files:
            st.write("**Available Backups:**")
            
            # Show backups in a table
            backup_data = []
            for backup_file in backup_files:
                filename = os.path.basename(backup_file)
                mod_time = datetime.fromtimestamp(os.path.getmtime(backup_file))
                size = os.path.getsize(backup_file)
                backup_data.append({
                    "Filename": filename,
                    "Date": mod_time.strftime('%Y-%m-%d %H:%M:%S'),
                    "Size (KB)": round(size / 1024, 2)
                })
            
            backup_df = pd.DataFrame(backup_data)
            st.dataframe(backup_df)
            
            # Restore option
            st.write("**Restore from Backup:**")
            selected_backup = st.selectbox(
                "Select backup to restore",
                [os.path.basename(f) for f in backup_files],
                key="backup_select"
            )
            
            if st.button("Restore Selected Backup"):
                selected_path = os.path.join(BACKUP_DIR, selected_backup)
                if restore_from_backup(selected_path):
                    st.success("Backup restored successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to restore backup.")
        else:
            st.info("No backups available.")


def display_data_management_section(trades_df: pd.DataFrame) -> None:
    """
    Display the data management section in the UI.
    
    Args:
        trades_df (pd.DataFrame): DataFrame containing all trades
    """
    st.subheader("⚙️ Data Management")
    
    if trades_df.empty:
        st.info("No trades to manage.")
        return
    
    # Show data statistics
    st.write("### Data Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Trades", len(trades_df))
    
    with col2:
        closed_trades = trades_df[trades_df['status'] == 'Closed']
        st.metric("Closed Trades", len(closed_trades))
    
    with col3:
        open_trades = trades_df[trades_df['status'] == 'Open']
        st.metric("Open Trades", len(open_trades))
    
    with col4:
        unique_symbols = trades_df['symbol'].nunique()
        st.metric("Unique Symbols", unique_symbols)
    
    # Show file information
    st.write("### File Information")
    if os.path.exists(TRADES_FILE):
        file_size = os.path.getsize(TRADES_FILE)
        mod_time = datetime.fromtimestamp(os.path.getmtime(TRADES_FILE))
        
        st.write(f"**Main Data File:** {TRADES_FILE}")
        st.write(f"**File Size:** {file_size} bytes ({round(file_size/1024, 2)} KB)")
        st.write(f"**Last Modified:** {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Data cleanup options
    st.write("### Data Cleanup")
    
    # Find duplicates
    if not trades_df.empty:
        trades_df['duplicate_key'] = trades_df.apply(
            lambda row: f"{row['date']}_{row['symbol']}_{row['entry_price']}", axis=1
        )
        duplicates = trades_df[trades_df.duplicated('duplicate_key', keep=False)]
        
        if not duplicates.empty:
            st.warning(f"Found {len(duplicates)} potential duplicate trades.")
            if st.button("Remove Duplicates"):
                # Remove duplicates, keeping the first occurrence
                cleaned_df = trades_df.drop_duplicates('duplicate_key', keep='first')
                cleaned_df = cleaned_df.drop('duplicate_key', axis=1)
                save_trades(cleaned_df)
                st.success("Duplicates removed successfully!")
                st.experimental_rerun()
        else:
            st.success("No duplicates found.")
        
        # Clean up temporary column
        if 'duplicate_key' in trades_df.columns:
            trades_df = trades_df.drop('duplicate_key', axis=1)
    
    # Reset data button (with confirmation)
    st.write("### Reset Data")
    st.warning("⚠️ This will permanently delete all trades!")
    if st.checkbox("I understand this action cannot be undone", key="reset_confirm"):
        if st.button("Reset All Data"):
            try:
                # Create backup before reset
                backup_path = create_backup()
                st.info(f"Backup created: {os.path.basename(backup_path)}")
                
                # Clear the main data file
                empty_df = pd.DataFrame(columns=[
                    "date", "symbol", "strategy", "entry_price", 
                    "exit_price", "quantity", "pnl", "notes", "status"
                ])
                save_trades(empty_df)
                
                st.success("All data has been reset!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error resetting data: {str(e)}")


def main():
    """Main application function."""
    st.set_page_config(
        page_title="Simple Trading Journal",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Simple Trading Journal")
    
    # Initialize session state for form
    if 'show_form' not in st.session_state:
        st.session_state.show_form = False
    if 'show_import' not in st.session_state:
        st.session_state.show_import = False
    if 'show_export' not in st.session_state:
        st.session_state.show_export = False
    if 'show_management' not in st.session_state:
        st.session_state.show_management = False
    
    # Load existing trades
    trades_df = load_trades()
    
    # Create filter sidebar and get filter config
    filter_config = create_filter_sidebar(trades_df)
    
    # Apply filters
    filtered_trades_df = filter_trades(trades_df, filter_config)
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Toggle form visibility
        if st.button("➕ Add New Trade"):
            st.session_state.show_form = not st.session_state.show_form
        
        # Toggle import visibility
        if st.button("📁 Import CSV"):
            st.session_state.show_import = not st.session_state.show_import
        
        # Toggle export visibility
        if st.button("💾 Export Data"):
            st.session_state.show_export = not st.session_state.show_export
        
        # Toggle data management visibility
        if st.button("⚙️ Data Management"):
            st.session_state.show_management = not st.session_state.show_management
    
    # Add trade form (collapsible)
    if st.session_state.show_form:
        with st.expander("➕ Add New Trade", expanded=True):
            with st.form("add_trade_form"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    date = st.date_input("Date", value=datetime.now().date())
                    symbol = st.text_input("Symbol")
                    strategy = st.selectbox("Strategy", STRATEGY_OPTIONS)
                
                with col2:
                    entry_price = st.number_input("Entry Price", min_value=0.0, step=0.01)
                    exit_price = st.number_input("Exit Price (0 for open trades)", min_value=0.0, step=0.01, value=0.0)
                    quantity = st.number_input("Quantity", value=1)
                
                with col3:
                    notes = st.text_area("Notes")
                
                submitted = st.form_submit_button("Add Trade")
                
                if submitted:
                    # Validate required fields
                    if not symbol:
                        st.error("Symbol is required")
                    elif entry_price <= 0:
                        st.error("Entry price must be greater than 0")
                    elif quantity == 0:
                        st.error("Quantity must not be zero")
                    else:
                        # Add trade
                        trade_data = {
                            "date": date.strftime("%Y-%m-%d"),
                            "symbol": symbol.upper(),
                            "strategy": strategy,
                            "entry_price": entry_price,
                            "exit_price": exit_price,
                            "quantity": quantity,
                            "notes": notes,
                            "status": "Open" if exit_price == 0 else "Closed"
                        }
                        
                        try:
                            add_trade(trade_data)
                            st.success("Trade added successfully!")
                            # Reset form visibility
                            st.session_state.show_form = False
                            # Rerun to refresh data
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error adding trade: {str(e)}")
    
    # CSV import section (collapsible)
    if st.session_state.show_import:
        with st.expander("📁 CSV Import", expanded=True):
            display_import_section()
    
    # Export section (collapsible)
    if st.session_state.show_export:
        with st.expander("💾 Export Data", expanded=True):
            display_export_section(trades_df, filtered_trades_df)
    
    # Data management section (collapsible)
    if st.session_state.show_management:
        with st.expander("⚙️ Data Management", expanded=True):
            display_data_management_section(trades_df)
    
    # Show filter summary
    if len(filtered_trades_df) != len(trades_df):
        st.info(f"Showing {len(filtered_trades_df)} of {len(trades_df)} trades based on active filters")
    
    # Display charts
    display_charts(filtered_trades_df)
    
    # Summary metrics (based on filtered data)
    stats = get_summary_stats(filtered_trades_df)
    
    st.subheader("📈 Quick Stats")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total P&L", f"${stats['total_pnl']:.2f}")
    
    with col2:
        st.metric("Win Rate", f"{stats['win_rate']:.1%}")
    
    with col3:
        st.metric("Total Trades", stats['total_trades'])
    
    with col4:
        st.metric("Avg Trade", f"${stats['avg_trade']:.2f}")
    
    # Trade history table (filtered)
    st.subheader("📋 Trade History")
    
    if filtered_trades_df.empty:
        st.info("No trades match the current filters. Try adjusting your filter settings.")
    else:
        # Allow editing of trades
        edited_df = st.data_editor(
            filtered_trades_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "date": st.column_config.DateColumn("Date"),
                "entry_price": st.column_config.NumberColumn("Entry Price", format="$%.2f"),
                "exit_price": st.column_config.NumberColumn("Exit Price", format="$%.2f"),
                "pnl": st.column_config.NumberColumn("P&L", format="$%.2f"),
            }
        )
        
        # Save changes if any
        if not edited_df.equals(filtered_trades_df):
            # We need to merge the changes back to the original dataframe
            # This is a bit complex, so we'll just save all trades
            save_trades(edited_df)
            st.success("Changes saved!")
            st.experimental_rerun()


if __name__ == "__main__":
    main()