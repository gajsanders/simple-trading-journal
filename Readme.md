# Simple Trading Journal

A lightweight, personal trading journal built with Streamlit for quick trade entry, basic performance tracking, and simple note-taking.

## Features

- **Manual Trade Entry**: Simple form-based trade input with validation
- **CSV Import/Export**: Flexible data import with column mapping
- **Performance Analytics**: Win rate, P&L tracking, and key metrics
- **Interactive Charts**: P&L over time and performance visualizations
- **Data Filtering**: Filter by date, symbol, strategy, and status
- **Local Storage**: All data stored locally in CSV format
- **Single File**: Lightweight, portable application

## Quick Start

### Installation

1. **Clone or download this repository**
git clone <repository-url>
cd simple-trading-journal

text

2. **Install dependencies**
pip install -r requirements.txt

text

3. **Run the application**
streamlit run app.py

text

The application will open in your default web browser at `http://localhost:8501`

### First Use

1. Click "Add New Trade" to create your first trade entry
2. Fill in the required fields (Date, Symbol, Strategy, Entry Price, Quantity)
3. Click "Add Trade" to save
4. View your trade in the table below and track your performance metrics

## Usage Guide

### Adding Trades

**Required Fields:**
- **Date**: Trade execution date
- **Symbol**: Stock ticker or instrument symbol
- **Strategy**: Select from predefined strategies
- **Entry Price**: Price at which you entered the position
- **Quantity**: Number of shares/contracts (negative for short positions)

**Optional Fields:**
- **Exit Price**: Leave blank for open positions
- **Notes**: Additional information about the trade

### Strategies Supported

- Long Stock
- Short Stock  
- Long Call
- Short Call
- Long Put
- Short Put
- Covered Call
- Cash Secured Put
- Other

### Data Management

**CSV Import:**
- Upload CSV files with trade data
- Map columns to required fields
- Preview data before importing
- Handle duplicate detection

**Export Options:**
- Export all trades or filtered subset
- Download as CSV for external analysis
- Create backups of your data

### Analytics

**Key Metrics:**
- Total P&L
- Win Rate
- Average Trade
- Number of Trades
- Open vs Closed positions

**Charts:**
- P&L over time
- Performance by strategy
- Win/loss distribution

## File Structure

simple-trading-journal/
├── app.py # Main application
├── requirements.txt # Dependencies
├── data/ # Auto-created data directory
│ └── trades.csv # Your trade data
└── README.md # This file

text

## Data Format

Your trades are stored in `data/trades.csv` with the following format:

date,symbol,strategy,entry_price,exit_price,quantity,pnl,notes,status
2025-01-15,AAPL,Long Stock,150.00,155.00,100,500.00,Good earnings,Closed
2025-01-16,GOOGL,Long Stock,2800.00,0.00,10,0.00,Holding for earnings,Open

text

## Requirements

- Python 3.9 or higher
- Streamlit 1.28.0+
- Pandas 2.0.0+
- Modern web browser

## Troubleshooting

**Application won't start:**
- Ensure Python 3.9+ is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Check for port conflicts: try `streamlit run app.py --server.port 8502`

**Data not saving:**
- Check file permissions in the project directory
- Ensure `data/` directory can be created
- Verify CSV file is not open in another application

**Import not working:**
- Ensure CSV file has proper headers
- Check for special characters in data
- Verify date format is YYYY-MM-DD
- Try mapping columns manually

## Contributing

This is a personal trading journal application. If you find bugs or have suggestions:

1. Check existing issues
2. Create detailed bug reports
3. Suggest improvements with use cases

## License

This project is for personal use. Modify and distribute as needed.

## Disclaimer

This application is for trade tracking purposes only. It does not provide financial advice. Always consult with qualified financial professionals for investment decisions.