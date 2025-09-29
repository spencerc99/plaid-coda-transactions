import requests
import os
import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env")
# TODO: command line utility to prompt for these things and setup in `.env`
### CONSTANTS
doc_id = os.getenv("CODA_DOC_ID")  # something like "4aBCsjYtC"
base_uri = "https://coda.io/apis/v1"
headers = {"Authorization": f'Bearer {os.getenv("CODA_API_KEY")}'}
transaction_table_id = os.getenv("CODA_TRANSACTIONS_TABLE_ID")
source_column_id = os.getenv("CODA_TRANSACTIONS_TABLE_SOURCE_COL_ID")
last_transaction_date_col_id = os.getenv("CODA_LAST_TRANSACTION_DATE_COL_ID")
last_transaction_id_col_id = os.getenv("CODA_LAST_TRANSACTION_ID_COL_ID")
bank_table_id = os.getenv("CODA_BANK_TABLE_ID")

# TODO: grab this automatically
key_to_column_id = {
    "amount": "c-yUu7YUw06j",
    "category": "c-XpUwNIUJpv",
    "name": "c-IZHxZWF-1A",
    "datetime": "c-zVCv3YQB7I",  # Store full datetime instead of just date for proper lastTransactionId functionality
    "transaction_id": "c-Bxu6HBEvtR",
    "city": "c-oJHUt-5ZE2",
    "country": "c-5ML0PHB1ML",
}


def format_none(val):
    return "" if val is None else val


### HELPERS FOR A BANK
def format_transaction_value_to_coda_column(key, transaction):
    return getattr(transaction, key)


def format_transactions_into_rows(bank, transactions):
    rows = []
    for transaction in transactions:
        row = [{"column": source_column_id, "value": bank}]
        for k, col_id in key_to_column_id.items():
            col = {}
            col["column"] = col_id
            col["value"] = format_none(
                format_transaction_value_to_coda_column(k, transaction)
            )
            row.append(col)
        rows.append({"cells": row})
    return {"rows": rows}


def add_transactions(bank, transactions):
    if not len(transactions):
        print(f"No new transactions for bank {bank}")
        return
    json_rows = format_transactions_into_rows(bank, transactions)
    print(f"Adding {len(json_rows['rows'])} transactions for bank {bank}")
    req = requests.post(
        f"{base_uri}/docs/{doc_id}/tables/{transaction_table_id}/rows",
        json=json_rows,
        headers=headers,
    )
    print(req.text)
    req.raise_for_status()


def get_last_transaction_date_for_bank(bank):
    """
    bank -- can be the name of the bank (brittle) or the rowId associated with it in the
    Coda Doc.
    
    Returns the full datetime and last transaction ID.
    Fixed to return datetime instead of just date for proper transaction ordering.
    """
    print(f"""{"*" * 50}
*{(46 - len(bank)) // 2 * " "} {bank} {(46 - len(bank)) // 2 * " "}*
{"*" * 50}""")
    print("Retrieving last known transaction datetime...")
    req = requests.get(
        f"{base_uri}/docs/{doc_id}/tables/{bank_table_id}/rows/{bank}", headers=headers
    )
    req.raise_for_status()
    resp = req.json()
    last_datetime = resp["values"][last_transaction_date_col_id]
    last_transaction_id = resp["values"][last_transaction_id_col_id]
    
    # Extract just the date part for display, but return full datetime for API calls
    display_date = last_datetime.split("T")[0] if "T" in last_datetime else last_datetime
    print(f"Last known transaction on {display_date} with ID {last_transaction_id}")
    print(f"Full datetime: {last_datetime}")
    
    return last_datetime, last_transaction_id


def get_existing_transaction_ids_for_bank(bank, start_date=None, end_date=None):
    """
    Get transaction IDs that already exist in Coda for a specific bank and date range.
    This is much more efficient than fetching all transactions.
    
    Args:
        bank: Bank name to filter by
        start_date: Optional start date (YYYY-MM-DD) to limit the search
        end_date: Optional end date (YYYY-MM-DD) to limit the search
    """
    print(f"Retrieving existing transaction IDs for {bank}", end="")
    if start_date and end_date:
        print(f" (date range: {start_date} to {end_date})")
    else:
        print(" (all dates)")
    
    # Build query parameters for efficient server-side filtering
    params = {
        "useColumnNames": True,
        "limit": 1000,  # Fetch in reasonable batches
        "query": bank,  # Filter by bank name on server side - much more efficient!
    }
    
    existing_ids = set()
    next_page_token = None
    total_rows_fetched = 0
    
    try:
        while True:
            current_params = params.copy()
            if next_page_token:
                current_params["pageToken"] = next_page_token
            
            req = requests.get(
                f"{base_uri}/docs/{doc_id}/tables/{transaction_table_id}/rows",
                headers=headers,
                params=current_params
            )
            req.raise_for_status()
            resp = req.json()
            
            rows_in_batch = len(resp.get("items", []))
            total_rows_fetched += rows_in_batch
            rows_processed = 0
            
            for row in resp.get("items", []):
                values = row.get("values", {})
                
                # Double-check bank filter (server-side query should handle this, but be safe)
                if values.get("Source") != bank:
                    continue
                    
                # If we have date filters, check the date
                if start_date or end_date:
                    transaction_date = values.get("Date")
                    if transaction_date:
                        # Extract date part (Coda might return datetime)
                        if "T" in transaction_date:
                            transaction_date = transaction_date.split("T")[0]
                        
                        # Filter by date range if specified
                        if start_date and transaction_date < start_date:
                            continue
                        if end_date and transaction_date > end_date:
                            continue
                
                transaction_id = values.get("Transaction ID")
                if transaction_id:
                    existing_ids.add(transaction_id)
                    rows_processed += 1
            
            print(f"   Batch: {rows_in_batch} rows fetched, {rows_processed} relevant for date range")
            
            # Check if there are more pages
            next_page_token = resp.get("nextPageToken")
            if not next_page_token:
                break
                
            # Safety check to prevent infinite loops
            if total_rows_fetched > 10000:
                print(f"   ⚠️  Safety limit reached ({total_rows_fetched} rows) - stopping fetch")
                break
        
        print(f"✅ Found {len(existing_ids)} existing transactions for {bank} (scanned {total_rows_fetched} total rows)")
        return existing_ids
        
    except Exception as e:
        print(f"\n❌ Error fetching existing transactions: {e}")
        # Fallback: return empty set to allow import (will result in potential duplicates)
        print("⚠️  Continuing without duplicate check - may create duplicates!")
        return set()


def check_transactions_exist_batch(bank, transaction_ids_batch):
    """
    Check if a small batch of transaction IDs already exist in Coda.
    This is more efficient for very large imports where even fetching existing IDs is slow.
    
    Args:
        bank: Bank name
        transaction_ids_batch: List of transaction IDs to check (keep small, e.g., 50-100)
    
    Returns:
        Set of transaction IDs that already exist
    """
    if not transaction_ids_batch:
        return set()
    
    # Use a more targeted query to check just these specific transaction IDs
    # Note: This might require iterating through results, but with smaller dataset
    params = {
        "useColumnNames": True,
        "limit": min(len(transaction_ids_batch) * 2, 500),  # Reasonable limit
        "query": bank,  # Filter by bank first
    }
    
    existing_in_batch = set()
    
    try:
        req = requests.get(
            f"{base_uri}/docs/{doc_id}/tables/{transaction_table_id}/rows",
            headers=headers,
            params=params
        )
        req.raise_for_status()
        resp = req.json()
        
        for row in resp.get("items", []):
            values = row.get("values", {})
            if values.get("Source") == bank:
                transaction_id = values.get("Transaction ID")
                if transaction_id in transaction_ids_batch:
                    existing_in_batch.add(transaction_id)
        
        return existing_in_batch
        
    except Exception as e:
        print(f"⚠️  Error checking batch: {e}")
        return set()  # Assume none exist to avoid blocking import


def add_transactions_with_batch_duplicate_check(bank, transactions, batch_size=50):
    """
    Alternative approach: Add transactions in batches, checking duplicates for each batch.
    This is more efficient for very large transaction lists.
    
    Args:
        bank: Bank name
        transactions: List of Transaction objects
        batch_size: Size of batches to process (smaller = more API calls but less memory)
    """
    if not len(transactions):
        print(f"No new transactions for bank {bank}")
        return
    
    print(f"Processing {len(transactions)} transactions in batches of {batch_size}")
    
    total_added = 0
    total_skipped = 0
    
    # Process transactions in batches
    for i in range(0, len(transactions), batch_size):
        batch = transactions[i:i + batch_size]
        batch_ids = [t.transaction_id for t in batch]
        
        print(f"  Checking batch {i//batch_size + 1}/{(len(transactions) + batch_size - 1)//batch_size} ({len(batch)} transactions)")
        
        # Check which ones already exist
        existing_ids = check_transactions_exist_batch(bank, batch_ids)
        
        # Filter to only new transactions
        new_transactions = [
            t for t in batch 
            if t.transaction_id not in existing_ids
        ]
        
        skipped_in_batch = len(batch) - len(new_transactions)
        total_skipped += skipped_in_batch
        
        if new_transactions:
            print(f"    Adding {len(new_transactions)} new transactions (skipping {skipped_in_batch} duplicates)")
            add_transactions(bank, new_transactions)
            total_added += len(new_transactions)
        else:
            print(f"    All {len(batch)} transactions already exist")
    
    print(f"✅ Batch processing complete: {total_added} added, {total_skipped} skipped")


def add_transactions_with_duplicate_check(bank, transactions, start_date=None, end_date=None):
    """
    Add transactions to Coda, skipping any that already exist based on transaction_id.
    
    Args:
        bank: Bank name
        transactions: List of Transaction objects
        start_date: Optional start date for efficient duplicate checking
        end_date: Optional end date for efficient duplicate checking
    """
    if not len(transactions):
        print(f"No new transactions for bank {bank}")
        return
    
    # For very large datasets (>1000 transactions), use batch processing for better efficiency
    if len(transactions) > 1000:
        print(f"Large dataset detected ({len(transactions)} transactions). Using batch processing for efficiency.")
        return add_transactions_with_batch_duplicate_check(bank, transactions)
    
    # Get existing transaction IDs to avoid duplicates (only for the date range if specified)
    existing_ids = get_existing_transaction_ids_for_bank(bank, start_date, end_date)
    
    # Filter out transactions that already exist
    new_transactions = [
        t for t in transactions 
        if t.transaction_id not in existing_ids
    ]
    
    if not new_transactions:
        print(f"All {len(transactions)} transactions for {bank} already exist in Coda")
        return
    
    print(f"Skipping {len(transactions) - len(new_transactions)} duplicate transactions")
    print(f"Adding {len(new_transactions)} new transactions for bank {bank}")
    
    # Use existing function to add the new transactions
    return add_transactions(bank, new_transactions)


def reimport_bank_transactions_with_duplicate_check(
    bank, 
    start_date, 
    end_date
):
    """
    Re-import transactions for a date range, skipping duplicates.
    This is useful for fixing missing transactions without creating duplicates.
    """
    print(f"\n{'='*60}")
    print(f"RE-IMPORTING TRANSACTIONS FOR {bank}")
    print(f"Date range: {start_date} to {end_date}")
    print(f"{'='*60}")
    
    # Import transactions for the specified date range
    # We don't pass last_transaction_id since we want all transactions in the range
    if bank == "Venmo":
        import venmo
        transactions = venmo.get_transactions(
            last_transaction_id=None,  # Don't filter by last transaction ID
            start_transaction_ts=datetime.datetime.strptime(
                start_date, "%Y-%m-%d"
            ).timestamp(),
            end_transaction_ts=datetime.datetime.strptime(
                end_date, "%Y-%m-%d"
            ).timestamp(),
        )
    else:
        from plaid_helpers import get_transactions
        from store import Store
        store = Store("plaid_codes.json")
        transactions = get_transactions(
            store, bank, start_date, end_date, last_transaction_id=None
        )
    
    # Add transactions with duplicate checking, passing the date range for efficiency
    return add_transactions_with_duplicate_check(bank, transactions, start_date, end_date)
