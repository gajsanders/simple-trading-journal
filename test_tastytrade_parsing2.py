import pandas as pd
from app import parse_tastytrade_row

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

# Parse the row
result = parse_tastytrade_row(row)
print("\nParsed result:")
print(result)

# Expected result should be:
# - Strategy: Cash Secured Put (because of STO)
# - Quantity: -2 (from description)
# - Entry price: 1.06 (credit received)
# - Status: Open (since it's STO)