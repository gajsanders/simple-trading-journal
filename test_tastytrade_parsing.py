import pandas as pd
from app import parse_tastytrade_row

# Read the test Tastytrade CSV file
df = pd.read_csv("test_tastytrade.csv")

print("Testing Tastytrade parsing...")
print(f"Number of rows: {len(df)}")
print()

# Test parsing each row
for idx, row in df.iterrows():
    print(f"Row {idx + 1}:")
    print(f"  Original data: {row.to_dict()}")
    
    # Parse the row
    parsed_data = parse_tastytrade_row(row)
    
    if parsed_data:
        print(f"  Parsed data: {parsed_data}")
    else:
        print("  Failed to parse row")
    
    print()