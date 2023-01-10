from tqdm import tqdm
import traceback
from plaid_helpers import get_transactions
from coda import (
    add_transactions as add_transactions_to_coda,
    get_last_transaction_date_for_bank,
)
from store import Store
import datetime
import json
import time
import venmo
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
    # use different method based on bank info, for now just special case venmo
    if bank == "Venmo":
        transactions = venmo.get_transactions(
            last_transaction_id=last_transaction_id,
            start_transaction_ts=datetime.datetime.strptime(
                start_date, "%Y-%m-%d"
            ).timestamp(),
            end_transaction_ts=datetime.datetime.strptime(
                end_date, "%Y-%m-%d"
            ).timestamp(),
        )
    else:
        transactions = get_transactions(
            store, bank, start_date, end_date, last_transaction_id
        )
    return add_transactions_to_coda(bank, transactions)


def update_bank_transactions(
    bank,
    input_start_date=None,
    input_end_date="{:%Y-%m-%d}".format(datetime.datetime.now()),
):
    start_date, last_transaction_id = get_last_transaction_date_for_bank(bank)
    default_start_date = "{:%Y-%m-%d}".format(
        datetime.datetime.now() + datetime.timedelta(days=-30)
    )
    return add_bank_transactions(
        bank,
        start_date=input_start_date or start_date or default_start_date,
        last_transaction_id=last_transaction_id,
        end_date=input_end_date,
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
    for bank in tqdm(banks):
        try:
            if bank not in all_banks:
                print(
                    f"ERROR 🚨: bank {bank} not found in list of banks. Double check your `plaid_codes.json` file"
                )
                continue
            update_bank_transactions(bank)
            # update_bank_transactions(bank, "2021-11-05", "2021-11-05")
            # TODO: allow for custom date range
            # update_bank_transactions(
            #     bank,
            #     "{:%Y-%m-%d}".format(datetime.datetime(year=2021, month=8, day=2)),
            #     "{:%Y-%m-%d}".format(datetime.datetime(year=2021, month=8, day=30)),
            # )

        except Exception as e:
            print(
                f"Failed to process transactions for {bank}: {''.join(traceback.TracebackException.from_exception(e).format())}"
            )

