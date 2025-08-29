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
import json
import hashlib

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
CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

class TradeValidationError(Exception):
    """Raised when trade data fails validation."""
    pass

class StorageError(Exception):
    """Raised when file operations fail."""
    pass

def load_config() -> dict:
    """
    Load application configuration.
    
    Returns:
        dict: Configuration dictionary
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            # Return default config if there's an error
            pass
    
    # Default configuration
    return {
        "currency": "USD",
        "date_format": "YYYY-MM-DD", 
        "default_strategy": "Long Stock",
        "theme": "light",
        "auto_save_interval": 300,  # 5 minutes
        "backup_enabled": True
    }

def save_config(config: dict) -> None:
    """
    Save application configuration.
    
    Args:
        config (dict): Configuration dictionary
    """
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        raise StorageError(f"Failed to save configuration: {str(e)}")

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_trades() -> pd.DataFrame:
    """
    Load trades from CSV file.
    
    Returns:
        pd.DataFrame: DataFrame containing all trades
    """
    if os.path.exists(TRADES_FILE):
        try:
            return pd.read_csv(TRADES_FILE)
        except Exception as e:
            raise StorageError(f"Failed to load trades: {str(e)}")
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
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        df.to_csv(TRADES_FILE, index=False)
    except Exception as e:
        raise StorageError(f"Failed to save trades: {str(e)}")

def calculate_pnl(entry: float, exit: float, quantity: int, strategy: str = "Other") -> float:
    """
    Calculate profit/loss for a trade, accounting for options-specific logic.
    
    For Cash Secured Puts and Covered Calls:
    - entry_price: Premium received when selling the option
    - exit_price: Premium paid when buying back (0 for open positions)  
    - P&L = (Premium Received - Premium Paid) * |Quantity| * 100
    
    For Long options (Long Put, Long Call):
    - entry_price: Premium paid when buying the option
    - exit_price: Premium received when selling (0 for open positions)
    - P&L = (Premium Received - Premium Paid) * |Quantity| * 100
    
    For stocks:
    - P&L = (Exit Price - Entry Price) * Quantity

    Args:
        entry (float): Entry price
        exit (float): Exit price (0 for open trades)
        quantity (int): Number of shares/contracts
        strategy (str): Trading strategy

    Returns:
        float: Profit/loss value
    """
    # For open trades, P&L is always 0
    if exit == 0:
        return 0.0

    # For options strategies, multiply by 100 (each contract represents 100 shares)
    if strategy in ["Cash Secured Put", "Covered Call", "Long Put", "Long Call", "Short Put", "Short Call"]:
        multiplier = 100
        is_options = True
    else:
        multiplier = 1
        is_options = False

    if is_options:
        # For option selling strategies (Cash Secured Put, Covered Call)
        if strategy in ["Cash Secured Put", "Covered Call"]:
            # For sellers: entry = premium received, exit = premium paid to close
            # P&L = (Premium Received - Premium Paid) * |Quantity| * 100
            return (entry - exit) * abs(quantity) * multiplier
        
        # For option buying strategies (Long Put, Long Call)
        elif strategy in ["Long Put", "Long Call"]:
            # For buyers: entry = premium paid, exit = premium received when sold
            # P&L = (Premium Received - Premium Paid) * |Quantity| * 100
            return (exit - entry) * abs(quantity) * multiplier
            
        # For Short options (Short Put, Short Call) - similar to selling strategies
        else:  # Short Put, Short Call
            # For short options: entry = premium received, exit = premium paid to close
            return (entry - exit) * abs(quantity) * multiplier
    else:
        # For stock and other non-options strategies
        return (exit - entry) * quantity * multiplier

def validate_trade_data(trade_data: dict) -> None:
    """
    Validate trade data.
    
    Args:
        trade_data (dict): Dictionary containing trade information
        
    Raises:
        TradeValidationError: If validation fails
    """
    # Validate required fields
    if not trade_data.get('symbol'):
        raise TradeValidationError("Symbol is required")
    if not trade_data.get('strategy'):
        raise TradeValidationError("Strategy is required")

    # Validate numeric fields
    try:
        entry_price = float(trade_data.get('entry_price', 0))
        if entry_price <= 0:
            raise TradeValidationError("Entry price must be positive")
    except (ValueError, TypeError):
        raise TradeValidationError("Entry price must be a valid number")

    try:
        quantity = int(trade_data.get('quantity', 0))
        if quantity == 0:
            raise TradeValidationError("Quantity cannot be zero")
    except (ValueError, TypeError):
        raise TradeValidationError("Quantity must be a valid integer")

    # Validate exit price if provided
    exit_price = trade_data.get('exit_price', 0)
    if exit_price:
        try:
            float(exit_price)
        except (ValueError, TypeError):
            raise TradeValidationError("Exit price must be a valid number")

    # Updated business rules for better Cash Secured Put handling
    strategy = trade_data.get('strategy', '')
    quantity = trade_data.get('quantity', 0)
    
    # For option selling strategies, quantity can be positive or negative
    # but we'll be flexible since users might enter either way
    if strategy == "Short Stock" and quantity > 0:
        raise TradeValidationError("Short Stock requires negative quantity")
    elif strategy in ["Long Stock", "Long Call", "Long Put"] and quantity < 0:
        raise TradeValidationError(f"{strategy} requires positive quantity")

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
    # Validate trade data
    validate_trade_data(trade_data)
    
    df = load_trades()
    
    # Calculate PnL with strategy awareness
    trade_data['pnl'] = calculate_pnl(
        trade_data['entry_price'],
        trade_data['exit_price'],
        trade_data['quantity'],
        trade_data.get('strategy', 'Other')
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
        st.rerun()
    
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

def main():
    """Main application function."""
    # Load configuration
    config = load_config()
    
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
    if 'show_settings' not in st.session_state:
        st.session_state.show_settings = False
    if 'show_help' not in st.session_state:
        st.session_state.show_help = False
    
    # Load existing trades
    try:
        trades_df = load_trades()
    except StorageError as e:
        st.error(f"Error loading trades: {str(e)}")
        trades_df = pd.DataFrame(columns=[
            "date", "symbol", "strategy", "entry_price",
            "exit_price", "quantity", "pnl", "notes", "status"
        ])
    
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
        
        # Toggle settings visibility
        if st.button("⚙️ Settings"):
            st.session_state.show_settings = not st.session_state.show_settings
        
        # Toggle help visibility
        if st.button("❓ Help"):
            st.session_state.show_help = not st.session_state.show_help
    
    # Add trade form (collapsible)
    if st.session_state.show_form:
        with st.expander("➕ Add New Trade", expanded=True):
            with st.form("add_trade_form"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    date = st.date_input("Date", value=datetime.now().date())
                    symbol = st.text_input("Symbol")
                    strategy = st.selectbox(
                        "Strategy",
                        STRATEGY_OPTIONS,
                        index=STRATEGY_OPTIONS.index(config.get("default_strategy", "Long Stock"))
                    )
                
                with col2:
                    entry_price = st.number_input("Entry Price", min_value=0.0, step=0.01)
                    exit_price = st.number_input("Exit Price (0 for open trades)", min_value=0.0, step=0.01, value=0.0)
                    quantity = st.number_input("Quantity", value=1)
                
                with col3:
                    notes = st.text_area("Notes")
                
                # Add helper text for Cash Secured Puts and Covered Calls
                if strategy == "Cash Secured Put":
                    st.info("💡 For Cash Secured Puts: Enter the premium you RECEIVED as Entry Price, "
                            "and the premium you PAID to close as Exit Price (or 0 if still open)")
                elif strategy == "Covered Call":
                    st.info("💡 For Covered Calls: Enter the premium you RECEIVED as Entry Price, "
                            "and the premium you PAID to close as Exit Price (or 0 if still open)")
                elif strategy in ["Long Put", "Long Call"]:
                    st.info("💡 For Long Options: Enter the premium you PAID as Entry Price, "
                            "and the premium you RECEIVED when selling as Exit Price (or 0 if still open)")
                
                submitted = st.form_submit_button("Add Trade")
                
                if submitted:
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
                        st.rerun()
                    except TradeValidationError as e:
                        st.error(f"Validation error: {str(e)}")
                    except StorageError as e:
                        st.error(f"Storage error: {str(e)}")
                    except Exception as e:
                        st.error(f"Error adding trade: {str(e)}")
    
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
                "date": st.column_config.TextColumn("Date"),
                "entry_price": st.column_config.NumberColumn("Entry Price", format="$%.2f"),
                "exit_price": st.column_config.NumberColumn("Exit Price", format="$%.2f"),
                "pnl": st.column_config.NumberColumn("P&L", format="$%.2f"),
            }
        )
        
        # Save changes if any
        if not edited_df.equals(filtered_trades_df):
            try:
                save_trades(edited_df)
                st.success("Changes saved!")
                st.rerun()
            except StorageError as e:
                st.error(f"Error saving changes: {str(e)}")

if __name__ == "__main__":
    main()
