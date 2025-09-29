#!/usr/bin/env python3
"""
Script to re-import transactions for a specific date range while avoiding duplicates.

This is useful when:
1. Plaid missed some transactions during initial import
2. You want to backfill transactions for a specific period
3. You need to fix data gaps without creating duplicates

Usage:
    python reimport_transactions.py <bank_name> <start_date> <end_date>
    
Examples:
    python reimport_transactions.py "Chase" "2024-01-01" "2024-01-31"
    python reimport_transactions.py "Discover" "2023-12-01" "2023-12-31"
"""

import sys
import datetime
from coda import reimport_bank_transactions_with_duplicate_check
from store import Store


def validate_date(date_string):
    """Validate that date_string is in YYYY-MM-DD format"""
    try:
        datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def main():
    if len(sys.argv) != 4:
        print("Usage: python reimport_transactions.py <bank_name> <start_date> <end_date>")
        print("Date format: YYYY-MM-DD")
        print("\nExample:")
        print('python reimport_transactions.py "Chase" "2024-01-01" "2024-01-31"')
        print("\nAvailable banks:")
        
        try:
            store = Store("plaid_codes.json")
            banks = store.get_banks()
            for bank in banks:
                print(f"  - {bank}")
        except Exception as e:
            print(f"  Error reading banks: {e}")
        
        sys.exit(1)
    
    bank_name = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    
    # Validate dates
    if not validate_date(start_date):
        print(f"Error: Invalid start date '{start_date}'. Use YYYY-MM-DD format.")
        sys.exit(1)
    
    if not validate_date(end_date):
        print(f"Error: Invalid end date '{end_date}'. Use YYYY-MM-DD format.")
        sys.exit(1)
    
    # Validate date range
    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    
    if start_dt > end_dt:
        print("Error: Start date must be before or equal to end date.")
        sys.exit(1)
    
    # Validate bank exists
    try:
        store = Store("plaid_codes.json")
        banks = store.get_banks()
        if bank_name not in banks:
            print(f"Error: Bank '{bank_name}' not found.")
            print("Available banks:")
            for bank in banks:
                print(f"  - {bank}")
            sys.exit(1)
    except Exception as e:
        print(f"Error reading bank configuration: {e}")
        sys.exit(1)
    
    # Confirm the operation
    days_diff = (end_dt - start_dt).days + 1
    print(f"\nRe-importing transactions for:")
    print(f"  Bank: {bank_name}")
    print(f"  Date range: {start_date} to {end_date} ({days_diff} days)")
    print(f"  This will skip any transactions already in Coda.")
    
    response = input("\nProceed? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Operation cancelled.")
        sys.exit(0)
    
    # Perform the re-import
    try:
        reimport_bank_transactions_with_duplicate_check(bank_name, start_date, end_date)
        print(f"\n✅ Successfully completed re-import for {bank_name}")
    except Exception as e:
        print(f"\n❌ Error during re-import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 
