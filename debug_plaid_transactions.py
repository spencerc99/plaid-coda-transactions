#!/usr/bin/env python3
"""
Diagnostic script to help debug Plaid transaction fetching issues.

This script provides detailed information about what transactions Plaid returns
for a given date range, helping identify if transactions are being missed.

Usage:
    python debug_plaid_transactions.py <bank_name> <start_date> <end_date>
"""

import sys
import datetime
from plaid_helpers import client
from store import Store
import plaid


def validate_date(date_string):
    """Validate that date_string is in YYYY-MM-DD format"""
    try:
        datetime.datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def debug_plaid_fetch(bank_name, start_date, end_date):
    """Debug Plaid transaction fetching with detailed logging"""
    print(f"\n🔍 DEBUGGING PLAID FETCH FOR {bank_name}")
    print(f"Date range: {start_date} to {end_date}")
    print("=" * 60)
    
    try:
        store = Store("plaid_codes.json")
        access_token = store.get_bank(bank_name).access_code
        
        all_transactions = []
        offset = 0
        batch_size = 500
        batch_num = 1
        
        while True:
            print(f"\n📦 Fetching batch {batch_num} (offset: {offset})")
            
            transactions_resp = client.Transactions.get(
                access_token, 
                start_date, 
                end_date,
                offset=offset,
                count=batch_size
            )
            
            transactions = transactions_resp.get("transactions", [])
            total_available = transactions_resp.get("total_transactions", 0)
            
            print(f"   ✅ Received {len(transactions)} transactions")
            print(f"   📊 Total available: {total_available}")
            print(f"   📈 Cumulative fetched: {len(all_transactions) + len(transactions)}")
            
            if not transactions:
                print("   🏁 No more transactions to fetch")
                break
            
            # Show sample transaction data from this batch
            if transactions:
                sample_tx = transactions[0]
                print(f"   🔍 Sample transaction: {sample_tx['date']} - {sample_tx['name']} - ${sample_tx['amount']}")
                print(f"   📅 Date range in batch: {transactions[-1]['date']} to {transactions[0]['date']}")
            
            all_transactions.extend(transactions)
            
            # Check if we've fetched all transactions
            if len(all_transactions) >= total_available:
                print(f"   ✅ Fetched all {total_available} available transactions")
                break
                
            offset += batch_size
            batch_num += 1
            
            # Safety check to prevent infinite loops
            if batch_num > 20:
                print("   ⚠️  Safety limit reached - stopping fetch")
                break
        
        print(f"\n📋 FETCH SUMMARY:")
        print(f"   Total transactions fetched: {len(all_transactions)}")
        
        # Analyze the transactions
        if all_transactions:
            # Group by status
            pending_count = sum(1 for tx in all_transactions if tx.get("pending", False))
            processed_count = len(all_transactions) - pending_count
            
            print(f"   Pending transactions: {pending_count}")
            print(f"   Processed transactions: {processed_count}")
            
            # Show date range
            dates = [tx["date"] for tx in all_transactions]
            dates.sort()
            print(f"   Date range: {dates[0]} to {dates[-1]}")
            
            # Show daily distribution
            from collections import Counter
            daily_counts = Counter(dates)
            print(f"\n📅 DAILY TRANSACTION DISTRIBUTION:")
            for date in sorted(daily_counts.keys()):
                count = daily_counts[date]
                pending_for_date = sum(1 for tx in all_transactions 
                                     if tx["date"] == date and tx.get("pending", False))
                print(f"   {date}: {count} total ({count - pending_for_date} processed, {pending_for_date} pending)")
            
            # Check for gaps
            start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            current_dt = start_dt
            
            print(f"\n🕳️  CHECKING FOR DATE GAPS:")
            gaps_found = False
            while current_dt <= end_dt:
                date_str = current_dt.strftime("%Y-%m-%d")
                if date_str not in daily_counts:
                    print(f"   ⚠️  No transactions on {date_str}")
                    gaps_found = True
                current_dt += datetime.timedelta(days=1)
            
            if not gaps_found:
                print("   ✅ No gaps found - transactions exist for all dates in range")
            
        else:
            print("   ⚠️  No transactions found in this date range")
            
    except plaid.errors.PlaidError as e:
        print(f"\n❌ PLAID API ERROR:")
        print(f"   Error code: {e.code}")
        print(f"   Error type: {e.type}")
        print(f"   Message: {e.display_message or e.message}")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()


def main():
    if len(sys.argv) != 4:
        print("Usage: python debug_plaid_transactions.py <bank_name> <start_date> <end_date>")
        print("Date format: YYYY-MM-DD")
        print("\nExample:")
        print('python debug_plaid_transactions.py "Chase" "2024-01-01" "2024-01-31"')
        
        try:
            store = Store("plaid_codes.json")
            banks = store.get_banks()
            print("\nAvailable banks:")
            for bank in banks:
                print(f"  - {bank}")
        except Exception as e:
            print(f"Error reading banks: {e}")
        
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
    
    debug_plaid_fetch(bank_name, start_date, end_date)


if __name__ == "__main__":
    main() 
