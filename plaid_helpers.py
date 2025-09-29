from typing import List
from local_types import Transaction
import plaid
from dotenv import load_dotenv
import os
import datetime

load_dotenv(dotenv_path="./.env")

# Fill in your Plaid API keys - https://dashboard.plaid.com/account/keys
PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_PUBLIC_KEY = os.getenv("PLAID_PUBLIC_KEY")
# Use 'sandbox' to test with Plaid's Sandbox environment (username: user_good,
# password: pass_good)
# Use `development` to test with live users and credentials and `production`
# to go live
PLAID_ENV = os.getenv("PLAID_ENV", "sandbox")
# PLAID_PRODUCTS is a comma-separated list of products to use when initializing
# Link. Note that this list must contain 'assets' in order for the app to be
# able to create and retrieve asset reports.
PLAID_PRODUCTS = os.getenv("PLAID_PRODUCTS", "transactions")

# PLAID_COUNTRY_CODES is a comma-separated list of countries for which users
# will be able to select institutions from.
PLAID_COUNTRY_CODES = os.getenv("PLAID_COUNTRY_CODES", "US,CA,GB,FR,ES")

client = plaid.Client(
    client_id=PLAID_CLIENT_ID,
    secret=PLAID_SECRET,
    public_key=PLAID_PUBLIC_KEY,
    environment=PLAID_ENV,
    api_version="2019-05-29",
)


def format_error(e):
    return {
        "error": {
            "display_message": e.display_message,
            "error_code": e.code,
            "error_type": e.type,
            "error_message": e.message,
        }
    }

# TODO: migrate to `/sync` https://plaid.com/docs/api/products/transactions/#transactionssync
# should remove duplicates. also need to pull latest quickstart`
def get_transactions(
    store, item, start_date, end_date, last_transaction_id
) -> List[Transaction]:
    """
    date must be formatted as follows: '{:%Y-%m-%d}'.format(datetime.datetime.now())
    
    Fixed to handle pagination properly and use datetime for proper transaction ordering.
    This was causing missing transactions when fetching large date ranges (over a month).
    """
    print(f"Getting transactions for {item} between {start_date} and {end_date}")
    if last_transaction_id:
        print(f"Will filter transactions after last known ID: {last_transaction_id}")

    access_token = store.get_bank(item).access_code
    all_transactions = []
    offset = 0
    batch_size = 500  # Maximum allowed by Plaid
    
    try:
        while True:
            print(f"Fetching batch {offset//batch_size + 1} (offset: {offset})")
            
            transactions_resp = client.Transactions.get(
                access_token, 
                start_date, 
                end_date,
                offset=offset,
                count=batch_size
            )
            
            if "transactions" not in transactions_resp:
                raise Exception(
                    f"No transactions found or errored out. resp: {transactions_resp}"
                )

            transactions = transactions_resp["transactions"]
            if type(transactions) != list and transactions["error"]:
                # error occurred
                raise Exception(transactions["error"])

            # If no transactions returned, we've fetched all available
            if not transactions:
                break
                
            all_transactions.extend(transactions)
            
            # Check if we've fetched all transactions
            total_transactions = transactions_resp.get("total_transactions", 0)
            if len(all_transactions) >= total_transactions:
                break
                
            offset += batch_size
            
        print(f"Retrieved {len(all_transactions)} total transactions from Plaid")

        # ignore pending transactions
        transactions = sorted(
            [transaction for transaction in all_transactions if not transaction["pending"]],
            # Sort by datetime if available, otherwise by date
            key=lambda t: (
                t.get("datetime") or 
                t.get("authorized_datetime") or 
                (t["date"] + "T12:00:00Z")
            )
        )
        
        print(f"After filtering pending: {len(transactions)} transactions")
        
        # grab everything past the last known transaction since plaid only does date filtering at the day level.
        if last_transaction_id:
            print(f"Filtering transactions after last known ID: {last_transaction_id}")
            last_transaction_id_idx = next(
                iter(
                    [
                        i
                        for i, transaction in enumerate(transactions)
                        if transaction["transaction_id"] == last_transaction_id
                    ]
                ),
                None,
            )
            if last_transaction_id_idx is not None:
                transactions = transactions[last_transaction_id_idx + 1 :]
                print(f"After filtering by last transaction ID: {len(transactions)} transactions")
            else:
                print(f"Warning: Last transaction ID {last_transaction_id} not found in results")

        print(f"Final transaction count to process: {len(transactions)}")

        return [
            Transaction(
                amount=transaction["amount"],
                category=transaction["category"],
                name=transaction["name"],
                # Ensure we always have a datetime value - prefer datetime field, fallback to date + time
                datetime=(
                    transaction.get("datetime") or 
                    transaction.get("authorized_datetime") or 
                    (transaction["date"] + "T12:00:00Z")
                ),
                date=transaction["date"],  # date should always be present
                transaction_id=transaction["transaction_id"],
                city=transaction["location"]["city"],
                country=transaction["location"]["country"],
            )
            for transaction in transactions
        ]

    except plaid.errors.PlaidError as e:
        print(f"Plaid API Error: {format_error(e)}")
        raise
    except Exception as e:
        print(f"General Error in get_transactions: {str(e)}")
        raise
