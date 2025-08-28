Simple Trading Journal - Complete Technical Specification
🎯 Project Overview
Purpose: Lightweight, personal trading journal for quick trade entry, basic performance tracking, and simple note-taking without complex analytics overhead.

Target Users: Individual traders (all asset classes) who need basic trade logging and performance overview
Deployment: Local Streamlit application, single-file architecture

📋 Core Requirements
Data Input

Manual Entry: Simple form-based trade input

CSV Import: Basic CSV upload with flexible column mapping

Edit Capability: Inline editing of all trade records

Data Persistence: Local file storage (CSV format)

Core Data Model

python
@dataclass
class Trade:
    date: str          # Trade date
    symbol: str        # Ticker symbol
    strategy: str      # Manual dropdown selection
    entry_price: float # Entry price
    exit_price: float  # Exit price (optional for open trades)
    quantity: int      # Number of shares/contracts
    pnl: float        # Profit/Loss (auto-calculated)
    notes: str        # Free text notes
    status: str       # "Open" or "Closed"
Performance Tracking

Basic Metrics: Win rate, total P&L, number of trades

Simple Filtering: By date range, symbol, strategy, status

Visual Summary: Built-in Streamlit charts (line/bar charts)

🏗️ Technical Architecture
Technology Stack

Language: Python 3.9+

Web Framework: Streamlit (single page application)

Data Processing: pandas (basic operations only)

Storage: Local CSV files

Visualization: Streamlit native charts

File Structure

text
simple-trading-journal/
├── app.py              # Main Streamlit application (200-300 lines)
├── requirements.txt    # streamlit, pandas
├── data/
│   └── trades.csv     # Local data storage
└── README.md
Core Functions

python
# Essential functions only
def load_trades() -> pd.DataFrame
def save_trades(df: pd.DataFrame) -> None
def add_trade(trade_data: dict) -> None
def calculate_pnl(entry: float, exit: float, quantity: int) -> float
def get_summary_stats(df: pd.DataFrame) -> dict
🖥️ User Interface Design
Single Page Layout

text
┌─────────────────────────────────────────┐
│  📊 Simple Trading Journal              │
├─────────────────────────────────────────┤
│  ➕ Add New Trade (Expandable Form)     │
│  📁 Import CSV                          │
├─────────────────────────────────────────┤
│  📈 Quick Stats (3-4 Key Metrics)       │
│  📊 Simple P&L Chart                    │
├─────────────────────────────────────────┤
│  📋 Trade History (Editable Table)      │
│  🔍 Basic Filters (Date, Symbol, Status)│
├─────────────────────────────────────────┤
│  💾 Export Data                         │
└─────────────────────────────────────────┘
Key Interface Elements

Add Trade Form: Symbol, date, strategy dropdown, prices, quantity, notes

Editable Table: Direct editing with Streamlit's st.data_editor

Summary Cards: st.metric for key statistics

Simple Charts: st.line_chart for P&L over time

Export Button: st.download_button for CSV export

🔧 Implementation Details
Strategy Options (Predefined Dropdown)

Long Stock

Short Stock

Long Call

Short Call

Long Put

Short Put

Covered Call

Cash Secured Put

Other

Data Validation

Minimal validation: Required fields only

Error handling: Simple try/catch with user notifications

Data types: Basic pandas dtype enforcement

Performance Calculations

python
def calculate_metrics(trades_df):
    return {
        'total_pnl': trades_df['pnl'].sum(),
        'win_rate': len(trades_df[trades_df['pnl'] > 0]) / len(trades_df),
        'total_trades': len(trades_df),
        'avg_trade': trades_df['pnl'].mean()
    }
🚀 Development Phases
Phase 1: Core MVP (4-6 hours)

Single Streamlit file with manual trade entry

Basic editable table display

Simple P&L calculation and summary stats

Local CSV storage

Phase 2: Import/Export (2-3 hours)

CSV import with column mapping

Export functionality

Basic filtering (date range, symbol)

Phase 3: Polish (2-3 hours)

Simple charts (P&L over time, win/loss distribution)

Input validation and error handling

UI improvements and styling

📤 Deliverables
Output Capabilities

Live Dashboard: Real-time trade tracking and metrics

CSV Export: Full data export for external analysis

Data Persistence: Automatic save/load functionality

Success Criteria

Speed: Add new trade in under 30 seconds

Simplicity: No training required for basic functionality

Reliability: Data integrity with local file backup

Portability: Single file deployment, minimal dependencies