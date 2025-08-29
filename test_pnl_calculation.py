"""
Test script to verify P&L calculation for cash secured puts.
"""

import sys
sys.path.append('/Users/enceladus/Documents/simple-trading-journal')

from app import calculate_pnl

def test_cash_secured_put_pnl():
    """Test P&L calculation for cash secured puts."""
    print("Testing Cash Secured Put P&L calculation...")
    
    # Test case: Sell for $1.06, Buy back for $0.15
    # Expected profit: $1.06 - $0.15 = $0.91 per contract
    # Since each contract represents 100 shares, total profit = $0.91 * 100 = $91
    
    entry_price = 1.06  # Credit received when selling
    exit_price = 0.15   # Debit paid when buying back
    quantity = -1       # Sold 1 contract (negative for selling)
    strategy = "Cash Secured Put"
    
    pnl = calculate_pnl(entry_price, exit_price, quantity, strategy)
    
    print(f"Sell for ${entry_price}, Buy back for ${exit_price}")
    print(f"Quantity: {quantity} contract(s)")
    print(f"Strategy: {strategy}")
    print(f"Calculated P&L: ${pnl}")
    print(f"Expected P&L: $91.00")
    
    # Check if result matches expected
    if abs(pnl - 91.00) < 0.01:  # Allow for floating point precision
        print("PASS: P&L calculation is correct")
        return True
    else:
        print("FAIL: P&L calculation is incorrect")
        return False

def test_long_put_pnl():
    """Test P&L calculation for long puts."""
    print("\nTesting Long Put P&L calculation...")
    
    # Test case: Buy for $0.15, Sell for $1.06
    # Expected profit: $1.06 - $0.15 = $0.91 per contract
    # Since each contract represents 100 shares, total profit = $0.91 * 100 = $91
    
    entry_price = 0.15  # Debit paid when buying
    exit_price = 1.06   # Credit received when selling
    quantity = 1        # Bought 1 contract (positive for buying)
    strategy = "Long Put"
    
    pnl = calculate_pnl(entry_price, exit_price, quantity, strategy)
    
    print(f"Buy for ${entry_price}, Sell for ${exit_price}")
    print(f"Quantity: {quantity} contract(s)")
    print(f"Strategy: {strategy}")
    print(f"Calculated P&L: ${pnl}")
    print(f"Expected P&L: $91.00")
    
    # Check if result matches expected
    if abs(pnl - 91.00) < 0.01:  # Allow for floating point precision
        print("PASS: P&L calculation is correct")
        return True
    else:
        print("FAIL: P&L calculation is incorrect")
        return False

def test_covered_call_pnl():
    """Test P&L calculation for covered calls."""
    print("\nTesting Covered Call P&L calculation...")
    
    # Test case: Sell for $2.50, Buy back for $0.75
    # Expected profit: $2.50 - $0.75 = $1.75 per contract
    # Since each contract represents 100 shares, total profit = $1.75 * 100 = $175
    
    entry_price = 2.50  # Credit received when selling
    exit_price = 0.75   # Debit paid when buying back
    quantity = -1       # Sold 1 contract (negative for selling)
    strategy = "Covered Call"
    
    pnl = calculate_pnl(entry_price, exit_price, quantity, strategy)
    
    print(f"Sell for ${entry_price}, Buy back for ${exit_price}")
    print(f"Quantity: {quantity} contract(s)")
    print(f"Strategy: {strategy}")
    print(f"Calculated P&L: ${pnl}")
    print(f"Expected P&L: $175.00")
    
    # Check if result matches expected
    if abs(pnl - 175.00) < 0.01:  # Allow for floating point precision
        print("PASS: P&L calculation is correct")
        return True
    else:
        print("FAIL: P&L calculation is incorrect")
        return False

def test_long_call_pnl():
    """Test P&L calculation for long calls."""
    print("\nTesting Long Call P&L calculation...")
    
    # Test case: Buy for $0.75, Sell for $2.50
    # Expected profit: $2.50 - $0.75 = $1.75 per contract
    # Since each contract represents 100 shares, total profit = $1.75 * 100 = $175
    
    entry_price = 0.75  # Debit paid when buying
    exit_price = 2.50   # Credit received when selling
    quantity = 1        # Bought 1 contract (positive for buying)
    strategy = "Long Call"
    
    pnl = calculate_pnl(entry_price, exit_price, quantity, strategy)
    
    print(f"Buy for ${entry_price}, Sell for ${exit_price}")
    print(f"Quantity: {quantity} contract(s)")
    print(f"Strategy: {strategy}")
    print(f"Calculated P&L: ${pnl}")
    print(f"Expected P&L: $175.00")
    
    # Check if result matches expected
    if abs(pnl - 175.00) < 0.01:  # Allow for floating point precision
        print("PASS: P&L calculation is correct")
        return True
    else:
        print("FAIL: P&L calculation is incorrect")
        return False

def test_stock_pnl():
    """Test P&L calculation for stock trades."""
    print("\nTesting Stock P&L calculation...")
    
    # Test case: Buy at $150, Sell at $160, 10 shares
    # Expected profit: ($160 - $150) * 10 = $100
    
    entry_price = 150.00  # Bought at $150
    exit_price = 160.00   # Sold at $160
    quantity = 10         # Bought 10 shares
    strategy = "Long Stock"
    
    pnl = calculate_pnl(entry_price, exit_price, quantity, strategy)
    
    print(f"Buy at ${entry_price}, Sell at ${exit_price}")
    print(f"Quantity: {quantity} share(s)")
    print(f"Strategy: {strategy}")
    print(f"Calculated P&L: ${pnl}")
    print(f"Expected P&L: $100.00")
    
    # Check if result matches expected
    if abs(pnl - 100.00) < 0.01:  # Allow for floating point precision
        print("PASS: P&L calculation is correct")
        return True
    else:
        print("FAIL: P&L calculation is incorrect")
        return False

if __name__ == "__main__":
    print("Running P&L calculation tests...")
    
    results = []
    results.append(test_cash_secured_put_pnl())
    results.append(test_long_put_pnl())
    results.append(test_covered_call_pnl())
    results.append(test_long_call_pnl())
    results.append(test_stock_pnl())
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("All tests passed!")
    else:
        print("Some tests failed!")