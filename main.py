import base64
from plaid_helpers import get_transactions
from coda import (
    add_transactions as add_transactions_to_coda,
    get_last_transaction_date_for_bank,
)
from store import Store
import datetime
import json
import time
from flask import Flask
from flask import request
import sys

app = Flask(__name__)
store = Store("plaid_codes.json")


# TODO: allow programming of how far back to look for first time setup
def add_bank_transactions(
    bank,
    start_date="{:%Y-%m-%d}".format(
        datetime.datetime.now() + datetime.timedelta(days=-30)
    ),
    end_date="{:%Y-%m-%d}".format(datetime.datetime.now()),
    last_transaction_id=None,
):
    transactions = get_transactions(
        store, bank, start_date, end_date, last_transaction_id
    )
    # ignore pending transactions
    transactions = [
        transaction for transaction in transactions if not transaction.pending
    ]
    # grab everything past the last known transaction since plaid only does date filtering at the day level.
    if last_transaction_id:
        from pdb import set_trace

        set_trace()
        last_transaction_id_idx = [
            i
            for i, transaction in enumerate(transactions)
            if transaction["transaction_id"] == last_transaction_id
        ][0]
        if last_transaction_id_idx:
            transactions = transactions[last_transaction_id_idx + 1 :]
    return add_transactions_to_coda(bank, transactions)


def update_bank_transactions(bank):
    start_date, last_transaction_id = get_last_transaction_date_for_bank(bank)
    return add_bank_transactions(
        bank, start_date=start_date, last_transaction_id=last_transaction_id
    )


@app.route("/add_bank_transactions", methods=["POST"])
def add_bank_transactions_handler():
    bank = request.args.get("bank")
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    if bank is None:
        return "Bank not provided!", 400
    return add_bank_transactions(bank, start_date, end_date)

# TODO: change to use click
if __name__ == "__main__":
    all_banks = store.get_banks()
    [_, *inp_banks] = sys.argv
    banks = inp_banks if len(inp_banks) > 0 else all_banks
    for bank in banks:
        try:
            if bank not in all_banks:
                print(
                    f"ERROR 🚨: bank {bank} not found in list of banks. Double check your `plaid_codes.json` file"
                )
                continue
            update_bank_transactions(bank)
        except Exception as e:
            print(f"Failed to process transactions for {bank}: {e.with_traceback()}")
