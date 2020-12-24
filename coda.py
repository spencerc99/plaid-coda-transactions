import requests
import os
import datetime
from dotenv import load_dotenv

load_dotenv(dotenv_path="./.env")
doc_id = "4_uKg6jYtC"
base_uri = "https://coda.io/apis/v1"
# SETUP: grab table data
headers = {"Authorization": f'Bearer {os.getenv("CODA_API_KEY")}'}

transaction_table_id = "grid-C2XUv0rWdc"

key_to_column_id = {
    "amount": "c-yUu7YUw06j",
    "category": "c-XpUwNIUJpv",
    "name": "c-IZHxZWF-1A",
    "date": "c-zVCv3YQB7I",
    "transaction_id": "c-Bxu6HBEvtR",
    # "transaction_type": "c-rZaY8n9ttI",
    "city": "c-oJHUt-5ZE2",
    "country": "c-5ML0PHB1ML",
}


def format_none(val):
    return "" if val is None else val


coda_column_to_plaid_mapper = {
    "amount": lambda transaction: transaction["amount"],
    "category": lambda transaction: transaction["category"],
    "name": lambda transaction: transaction["name"],
    "date": lambda transaction: transaction["date"],
    "transaction_id": lambda transaction: transaction["transaction_id"],
    # "transaction_type": lambda transaction: transaction['name'],
    "city": lambda transaction: transaction["location"]["city"],
    "country": lambda transaction: transaction["location"]["country"],
}

source_column_id = "c-oP1ZL3vd46"

# helpers for a bank


def format_transactions_into_rows(bank, transaction_resp):
    rows = []
    if "transactions" not in transaction_resp:
        print(f"No transactions found or errored out. resp: {transaction_resp}")
    for transaction in transaction_resp["transactions"]:
        row = [{"column": source_column_id, "value": bank}]
        for k, col_id in key_to_column_id.items():
            col = {}
            col["column"] = col_id
            col["value"] = format_none(coda_column_to_plaid_mapper[k](transaction))
            row.append(col)
        rows.append({"cells": row})
    return {"rows": rows}


def add_transactions(bank, payload):
    json_rows = format_transactions_into_rows(bank, payload)
    print(f"Adding {len(json_rows['rows'])} transactions for bank {bank}")
    req = requests.post(
        f"{base_uri}/docs/{doc_id}/tables/{transaction_table_id}/rows",
        json=json_rows,
        headers=headers,
    )
    print(req.text)
    req.raise_for_status()


last_transaction_date_col_id = "c-g8XDK5eQPp"
bank_table_id = "grid-KViIDD_wdd"


def get_last_transaction_date_for_bank(bank):
    """
    bank -- can be the name of the bank (brittle) or the rowId associated with it in the
    Coda Doc.
    """
    print(f"Retrieving last known transaction date for bank {bank}")
    req = requests.get(
        f"{base_uri}/docs/{doc_id}/tables/{bank_table_id}/rows/{bank}", headers=headers
    )
    req.raise_for_status()
    resp = req.json()
    datetime = resp["values"][last_transaction_date_col_id]
    date = datetime.split("T")[0]
    return date
