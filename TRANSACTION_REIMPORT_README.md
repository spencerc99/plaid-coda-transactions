# Transaction Re-import and Debugging Tools

This document describes the new tools created to address Plaid transaction fetching issues and provide re-import capabilities.

## Problem Solved

The original code had issues where:

1. **Missing transactions**: Plaid's `/transactions/get` API has pagination limits (500 transactions per request). When fetching large date ranges (over a month), transactions were being missed because the code wasn't handling pagination properly.
2. **No duplicate protection**: There was no way to re-import transactions without creating duplicates in Coda.
3. **Difficult debugging**: No tools to diagnose what transactions Plaid was actually returning.

## New Files Created

### 1. `reimport_transactions.py`

**Purpose**: Re-import transactions for a specific date range while automatically skipping duplicates.

**Usage**:

```bash
python reimport_transactions.py <bank_name> <start_date> <end_date>
```

**Examples**:

```bash
python reimport_transactions.py "Chase" "2024-01-01" "2024-01-31"
python reimport_transactions.py "Discover" "2023-12-01" "2023-12-31"
```

**Features**:

- Validates bank names and dates
- Shows confirmation before proceeding
- Automatically skips duplicate transactions based on transaction_id
- Provides clear success/error feedback

### 2. `debug_plaid_transactions.py`

**Purpose**: Debug what transactions Plaid is actually returning for a given date range.

**Usage**:

```bash
python debug_plaid_transactions.py <bank_name> <start_date> <end_date>
```

**Features**:

- Shows detailed pagination information
- Displays daily transaction distribution
- Identifies date gaps where no transactions exist
- Shows pending vs processed transaction counts
- Helps diagnose Plaid API issues

## Code Improvements

### Enhanced `plaid_helpers.py`

- **Fixed pagination**: Now properly handles pagination to fetch ALL transactions in a date range
- **Better logging**: Shows progress for each batch fetched
- **Improved error handling**: More detailed error messages for debugging

### New functions in `coda.py`

- `get_existing_transaction_ids_for_bank()`: Gets all existing transaction IDs for a bank
- `add_transactions_with_duplicate_check()`: Adds transactions while skipping duplicates
- `reimport_bank_transactions_with_duplicate_check()`: Main re-import function

## Usage Scenarios

### Immediate Fix: Re-import Missing Transactions

If you noticed missing transactions for a specific period:

1. **First, debug what Plaid returns**:

   ```bash
   python debug_plaid_transactions.py "Chase" "2024-01-01" "2024-01-31"
   ```

   This will show you exactly what transactions Plaid has for that period.

2. **Re-import with duplicate protection**:
   ```bash
   python reimport_transactions.py "Chase" "2024-01-01" "2024-01-31"
   ```
   This will fetch ALL transactions from Plaid for that period and add only the ones not already in Coda.

### Ongoing Prevention: Updated Main Script

The updated `main.py` now uses the improved `plaid_helpers.py` with proper pagination, so future runs should capture all transactions.

## Technical Details

### Pagination Fix

The original code made only one API call to Plaid, which has a 500 transaction limit. For date ranges with more than 500 transactions, some were being silently missed.

The fix:

- Makes multiple API calls with proper offset/count parameters
- Continues until all transactions are fetched
- Provides detailed logging of the fetch process

### Efficient Duplicate Detection

**For smaller datasets (≤1000 transactions):**

- Fetches existing transaction IDs only for the specified date range
- Uses Coda's server-side filtering (`query` parameter) to reduce data transfer
- Filters by bank name on the server side for efficiency

**For larger datasets (>1000 transactions):**

- Automatically switches to batch processing mode
- Processes transactions in small batches (50 transactions each)
- Each batch makes minimal API calls to check only those specific transaction IDs
- Avoids memory issues and API rate limits

**Key optimizations:**

- ✅ **Server-side filtering**: Uses Coda's `query` parameter to filter by bank
- ✅ **Date range limiting**: Only checks transactions in the import date range
- ✅ **Pagination**: Handles large result sets with proper pagination
- ✅ **Batch processing**: Automatically switches to batch mode for large imports
- ✅ **Error handling**: Graceful fallback if duplicate checking fails
- ✅ **Memory efficient**: Processes data in manageable chunks

### Error Handling

- Validates all inputs before processing
- Provides detailed error messages
- Gracefully handles Plaid API errors
- Falls back gracefully if duplicate checking fails (continues import with warning)

## Migration Notes

- The original `main.py` functionality is preserved
- New tools are additive - they don't break existing workflows
- The system automatically chooses the most efficient duplicate checking method based on dataset size
- Consider migrating to Plaid's newer `/transactions/sync` API in the future (as noted in TODO comments)

## Performance Guidelines

**For small imports (< 1000 transactions):**

- Use `reimport_transactions.py` normally
- The system will use optimized date-range duplicate checking

**For large imports (> 1000 transactions):**

- The system automatically switches to batch processing
- Consider splitting very large date ranges into smaller chunks for better control
- Monitor API rate limits if importing many thousands of transactions

**For very large datasets (> 10,000 transactions):**

- Consider running imports during off-peak hours
- Split into multiple smaller date ranges
- The system includes safety limits to prevent runaway API calls

## Recommendations

1. **For immediate issues**: Use `reimport_transactions.py` to backfill missing data
2. **For debugging**: Use `debug_plaid_transactions.py` to understand what Plaid returns
3. **For prevention**: The updated `main.py` should prevent future pagination issues
4. **For large datasets**: The system automatically optimizes, but consider splitting very large ranges
5. **Future improvement**: Consider migrating to Plaid's `/transactions/sync` API for better duplicate handling

## DateTime Fix for Last Transaction ID

### Problem Fixed

Previously, the system only stored the date (YYYY-MM-DD) in Coda, not the full datetime. This caused issues with the `lastTransactionId` functionality because:

1. Multiple transactions on the same day couldn't be properly ordered
2. The "last" transaction determination was unreliable when several transactions occurred on the same day
3. This led to missed transactions or incorrect starting points for subsequent imports

### Solution Implemented

- **Updated Transaction class**: Now stores both `datetime` (full timestamp) and `date` (for backward compatibility)
- **Enhanced Plaid integration**: Uses Plaid's `datetime` field when available, falls back to `date + T12:00:00Z` if not
- **Fixed Coda storage**: Now stores full datetime in the Date column instead of just the date
- **Improved sorting**: Transactions are now sorted by full datetime for proper chronological order
- **Maintained API compatibility**: Plaid API calls still use YYYY-MM-DD format as required

### Benefits

- ✅ Accurate "last transaction" determination even with multiple transactions per day
- ✅ Proper chronological ordering of transactions
- ✅ More reliable incremental imports
- ✅ Better handling of same-day transaction batches
- ✅ Backward compatibility maintained

### Technical Details
