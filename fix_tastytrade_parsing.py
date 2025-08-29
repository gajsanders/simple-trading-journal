# Read the current app.py file
with open('/Users/enceladus/Documents/simple-trading-journal/app.py', 'r') as f:
    content = f.read()

# Define the old function
old_function = '''def parse_tastytrade_row(row) -> dict:
    """
    Parse a single row from Tastytrade CSV format.
    """
    try:
        symbol = str(row.get('Symbol', '')).upper().strip()
        if not symbol:
            return None

        price_str = str(row.get('Price', ''))
        price_parts = price_str.split()
        if price_parts:
            price_clean = ''.join(c for c in price_parts if c.isdigit() or c == '.')
            if price_clean:
                price = float(price_clean)
            else:
                return None
        else:
            return None

        description = str(row.get('Description', ''))
        status_text = str(row.get('Status', ''))
        time_info = str(row.get('Time', '')) or str(row.get('TimeStampAtType', ''))

        # Basic default date; improve parsing if actual timestamp available
        date = datetime.now().strftime('%Y-%m-%d')

        # Quantity: simple integer scan
        qty = 1
        qty_match = re.search(r'([+-]?\d+)', description)
        if qty_match:
            qty = int(qty_match.group(1))

        entry_price = price
        exit_price = 0.0
        trade_status = 'Open'
        if 'STC' in description or 'BTC' in description:
            trade_status = 'Closed'
            exit_price = entry_price  # Simplified; real fill pairing would differ

        # Determine strategy heuristically
        strategy = 'Other'
        if 'Put' in description:
            if 'STO' in description:
                strategy = 'Cash Secured Put'
            elif 'BTC' in description:
                strategy = 'Long Put'
            elif 'BTO' in description:
                strategy = 'Long Put'
            elif 'STC' in description:
                strategy = 'Cash Secured Put'
            else:
                strategy = 'Long Put' if qty > 0 else 'Cash Secured Put'
        elif 'Call' in description:
            if 'STO' in description:
                strategy = 'Covered Call'
            elif 'BTC' in description:
                strategy = 'Long Call'
            elif 'BTO' in description:
                strategy = 'Long Call'
            elif 'STC' in description:
                strategy = 'Covered Call'
            else:
                strategy = 'Long Call' if qty > 0 else 'Covered Call'
        elif any(word in description for word in ['Stock', 'Equity']):
            strategy = 'Long Stock' if qty > 0 else 'Short Stock'
        else:
            strategy = 'Long Stock' if qty > 0 else 'Short Stock'

        return {
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
    except Exception:
        return None'''

# Define the new function
new_function = '''def parse_tastytrade_row(row) -> dict:
    """
    Parse a single row from Tastytrade CSV format.
    """
    try:
        symbol = str(row.get('Symbol', '')).upper().strip()
        if not symbol:
            return None

        # Use MarketOrFill column for actual execution price
        price_str = str(row.get('MarketOrFill', ''))
        if not price_str:
            return None
            
        # Extract the numeric price value (before 'cr' or 'db')
        price_parts = price_str.split()
        if not price_parts:
            return None
            
        price_text = price_parts[0]  # Get the price part (e.g., "1.06" from "1.06 cr")
        price_clean = ''.join(c for c in price_text if c.isdigit() or c == '.')
        if not price_clean:
            return None
            
        price = float(price_clean)
        
        # Determine if this is a credit (cr) or debit (db)
        is_credit = 'cr' in price_str.lower()
        is_debit = 'db' in price_str.lower()

        description = str(row.get('Description', ''))
        time_info = str(row.get('Time', '')) or str(row.get('TimeStampAtType', ''))

        # Parse date from Time or TimeStampAtType
        date = parse_tastytrade_date(time_info)
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')

        # Quantity: parse from description (e.g., "-2" or "1")
        qty = 1
        qty_match = re.search(r'([+-]?\d+)', description)
        if qty_match:
            qty = int(qty_match.group(1))

        # Initialize prices
        entry_price = price
        exit_price = 0.0
        
        # Determine if this is an opening or closing trade
        trade_status = 'Open'
        is_closing_trade = 'STC' in description or 'BTC' in description
        
        if is_closing_trade:
            trade_status = 'Closed'
            exit_price = entry_price  # For now, use the same price; could be improved with pairing

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

        return {
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
    except Exception:
        return None


def parse_tastytrade_date(time_str: str) -> str:
    """
    Parse date from Tastytrade time string.
    
    Args:
        time_str (str): Time string from Tastytrade (e.g., "8:46:07p" or "7/15 4:20p")
        
    Returns:
        str: Date in YYYY-MM-DD format, or None if parsing fails
    """
    try:
        if not time_str:
            return None
            
        # Handle formats like "7/15 4:20p" or "8:46:07p"
        time_str = time_str.strip().lower()
        
        # If it's just a time like "8:46:07p", use today's date
        if ':' in time_str and not any(c.isdigit() for c in time_str.split()[0] if '/' in time_str.split()[0]):
            return datetime.now().strftime('%Y-%m-%d')
            
        # If it has a date like "7/15 4:20p"
        if ' ' in time_str:
            date_part = time_str.split()[0]  # Get "7/15"
            if '/' in date_part:
                parts = date_part.split('/')
                if len(parts) == 2:
                    month, day = parts
                    # Assume current year
                    year = datetime.now().year
                    return f"{year}-{int(month):02d}-{int(day):02d}"
                    
        return None
    except Exception:
        return None'''

# Replace the function
content = content.replace(old_function, new_function)

# Write the updated content back to the file
with open('/Users/enceladus/Documents/simple-trading-journal/app.py', 'w') as f:
    f.write(content)

print("Updated parse_tastytrade_row function in app.py")