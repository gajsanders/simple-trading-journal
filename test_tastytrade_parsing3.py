import pandas as pd
from app import parse_tastytrade_row

# Test cases
test_cases = [
    {
        'name': 'Cash Secured Put (STO)',
        'data': {
            'Symbol': 'ETHA',
            'MarketOrFill': '1.06 cr',
            'Description': '-2 Aug 15 30d 23 Put STO'
        }
    },
    {
        'name': 'Long Put (BTO)',
        'data': {
            'Symbol': 'ETHA',
            'MarketOrFill': '0.15 db',
            'Description': '2 Aug 15 30d 16 Put BTO'
        }
    },
    {
        'name': 'Covered Call (STO)',
        'data': {
            'Symbol': 'AAPL',
            'MarketOrFill': '2.50 cr',
            'Description': '-1 Sep 20 45d 150 Call STO'
        }
    },
    {
        'name': 'Long Call (BTC)',
        'data': {
            'Symbol': 'AAPL',
            'MarketOrFill': '0.75 db',
            'Description': '1 Sep 20 45d 150 Call BTC'
        }
    }
]

for test_case in test_cases:
    print("\n=== " + test_case['name'] + " ===")
    print("Input data:")
    for key, value in test_case['data'].items():
        print("  " + key + ": " + str(value))
    
    # Convert to pandas Series
    row = pd.Series(test_case['data'])
    
    # Parse the row
    result = parse_tastytrade_row(row)
    print("Parsed result:")
    print(result)