"""
Minimal Trading Journal Application
A lightweight trading journal built with Streamlit for personal trade tracking.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os


# Ensure data directory exists
DATA_DIR = "data"
TRADES_FILE = os.path.join(DATA_DIR, "trades.csv")


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
            st.error(f"Failed to load trades: {str(e)}")
            return pd.DataFrame()
    else:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=[
            "date", "symbol", "strategy", "entry_price", 
            "exit_price", "quantity", "pnl", "notes", "status"
        ])


def main():
    """Main application function."""
    st.set_page_config(
        page_title="Simple Trading Journal",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Simple Trading Journal")
    
    # Load existing trades
    trades_df = load_trades()
    
    # Summary metrics
    if not trades_df.empty:
        st.subheader("📈 Quick Stats")
        col1, col2, col3 = st.columns(3)
        
        total_pnl = trades_df['pnl'].sum()
        total_trades = len(trades_df)
        
        with col1:
            st.metric("Total P&L", f"${total_pnl:.2f}")
        
        with col2:
            st.metric("Total Trades", total_trades)
            
        with col3:
            st.metric("Avg Trade", f"${total_pnl/total_trades:.2f}" if total_trades > 0 else "$0.00")
    
    # Trade history table
    st.subheader("📋 Trade History")
    
    if trades_df.empty:
        st.info("No trades found. Add some trades to get started.")
    else:
        st.dataframe(trades_df, use_container_width=True)


if __name__ == "__main__":
    main()