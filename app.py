"""
Simple Trading Journal Application
A lightweight trading journal built with Streamlit for personal trade tracking.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional
import os


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
    
    # Load existing trades
    trades_df = load_trades()
    
    # Sidebar for controls
    with st.sidebar:
        st.header("Controls")
        
        # Toggle form visibility
        if st.button("➕ Add New Trade"):
            st.session_state.show_form = not st.session_state.show_form
        
        # Export button
        if not trades_df.empty:
            st.download_button(
                label="💾 Export Trades",
                data=trades_df.to_csv(index=False),
                file_name="trades_export.csv",
                mime="text/csv"
            )
    
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
    
    # Summary metrics
    stats = get_summary_stats(trades_df)
    
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
    
    # Trade history table
    st.subheader("📋 Trade History")
    
    if trades_df.empty:
        st.info("No trades recorded yet. Add your first trade using the form above.")
    else:
        # Allow editing of trades
        edited_df = st.data_editor(
            trades_df,
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
        if not edited_df.equals(trades_df):
            save_trades(edited_df)
            st.success("Changes saved!")
            trades_df = edited_df  # Update for any subsequent operations


if __name__ == "__main__":
    main()