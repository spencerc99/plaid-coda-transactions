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
    "date": "c-zVCv3YQB7I",
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
    """
    print(f"""{"*" * 50}
*{(46 - len(bank)) // 2 * " "} {bank} {(46 - len(bank)) // 2 * " "}*
{"*" * 50}""")
    print("Retrieving last known transaction date...")
    req = requests.get(
        f"{base_uri}/docs/{doc_id}/tables/{bank_table_id}/rows/{bank}", headers=headers
    )
    req.raise_for_status()
    resp = req.json()
    datetime = resp["values"][last_transaction_date_col_id]
    last_transaction_id = resp["values"][last_transaction_id_col_id]
    date = datetime.split("T")[0]
    print(f"Last known date on {date} with transaction {last_transaction_id}")
    return date, last_transaction_id
