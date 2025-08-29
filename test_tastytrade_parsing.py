import pandas as pd
import traceback
from datetime import datetime
import re

def parse_tastytrade_row_fixed(row):
    """
    Fixed version of parse_tastytrade_row
    """
    print("Starting parse_tastytrade_row_fixed")
    try:
        symbol = str(row.get('Symbol', '')).upper().strip()
        print(f"Symbol: {symbol}")
        if not symbol:
            print("No symbol, returning None")
            return None

        # Use MarketOrFill column for actual execution price
        price_str = str(row.get('MarketOrFill', ''))
        print(f"MarketOrFill string: {price_str}")
        if not price_str:
            print("No MarketOrFill string, returning None")
            return None
            
        # Extract the numeric price value (before 'cr' or 'db')
        price_parts = price_str.split()
        print(f"Price parts: {price_parts}")
        if not price_parts:
            print("No price parts, returning None")
            return None
            
        price_text = price_parts[0]  # Get the price part (e.g., "1.06" from "1.06 cr")
        print(f"Price text: {price_text}")
        price_clean = ''.join(c for c in price_text if c.isdigit() or c == '.')
        print(f"Price clean: {price_clean}")
        if not price_clean:
            print("No clean price, returning None")
            return None
            
        price = float(price_clean)
        print(f"Price: {price}")
        
        # Determine if this is a credit (cr) or debit (db)
        is_credit = 'cr' in price_str.lower()
        is_debit = 'db' in price_str.lower()
        print(f"Is credit: {is_credit}, Is debit: {is_debit}")

        description = str(row.get('Description', ''))
        print(f"Description: {description}")
        time_info = str(row.get('Time', '')) or str(row.get('TimeStampAtType', ''))
        print(f"Time info: {time_info}")

        # Parse date from Time or TimeStampAtType
        date = datetime.now().strftime('%Y-%m-%d')  # Simplified for now
        print(f"Date: {date}")

        # Quantity: parse from description (e.g., "-2" or "1")
        qty = 1
        qty_match = re.search(r'([+-]?\d+)', description)
        print(f"Quantity match: {qty_match}")
        if qty_match:
            qty = int(qty_match.group(1))
        print(f"Quantity: {qty}")

        # Initialize prices
        entry_price = price
        exit_price = 0.0
        
        # Determine if this is an opening or closing trade
        trade_status = 'Open'
        is_closing_trade = 'STC' in description or 'BTC' in description
        print(f"Is closing trade: {is_closing_trade}")
        
        if is_closing_trade:
            trade_status = 'Closed'
            exit_price = entry_price  # For now, use the same price; could be improved with pairing
        print(f"Trade status: {trade_status}")

        # Determine strategy heuristically
        strategy = 'Other'
        if 'Put' in description:
            if 'STO' in description:  # Sell to Open
                strategy = 'Cash Secured Put'
            elif 'BTC' in description:  # Buy to Close
                strategy = 'Long Put'
            elif 'BTO' in description:  # Buy to Open
                strategy = 'Long Put'
            elif 'STC' in description:  # Sell to Close
                strategy = 'Cash Secured Put'
            else:
                # Default logic based on action type
                strategy = 'Long Put' if qty > 0 else 'Cash Secured Put'
        elif 'Call' in description:
            if 'STO' in description:  # Sell to Open
                strategy = 'Covered Call'
            elif 'BTC' in description:  # Buy to Close
                strategy = 'Long Call'
            elif 'BTO' in description:  # Buy to Open
                strategy = 'Long Call'
            elif 'STC' in description:  # Sell to Close
                strategy = 'Covered Call'
            else:
                # Default logic based on action type
                strategy = 'Long Call' if qty > 0 else 'Covered Call'
        elif any(word in description for word in ['Stock', 'Equity']):
            strategy = 'Long Stock' if qty > 0 else 'Short Stock'
        else:
            strategy = 'Long Stock' if qty > 0 else 'Short Stock'
        print(f"Strategy: {strategy}")

        result = {
            'date': date,
            'symbol': symbol,
            'strategy': strategy,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': qty,
            'pnl': 0.0,
            'notes': description,
            'status': trade_status,
        }
        print(f"Result: {result}")
        return result
    except Exception as e:
        print(f"Exception in parse_tastytrade_row_fixed: {e}")
        traceback.print_exc()
        return None

# Test with a sample TastyTrade row
sample_data = {
    'Symbol': 'ETHA',
    'Status': 'Filled',
    'MarketOrFill': '1.06 cr',
    'Price': '1.06 cr',
    'TIF': 'Day',
    'Time': '8:46:07p',
    'TimeStampAtType': 'Fill',
    'Order #': '#395388728',
    'Description': '-2 Aug 15 30d 23 Put STO'
}

# Convert to pandas Series to simulate a row
row = pd.Series(sample_data)

print("Input data:")
for key, value in sample_data.items():
    print(f"  {key}: {value}")

# Parse the row with error handling
result = parse_tastytrade_row_fixed(row)
print("\nFinal result:")
print(result)