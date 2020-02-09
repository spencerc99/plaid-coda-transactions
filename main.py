import base64
from plaid_helpers import (
    get_transactions,
)
from coda import (
    add_transactions as add_transactions_to_coda,
    get_last_transaction_date_for_bank
)
from store import (Store)
import datetime
import json
import time
from flask import Flask
from flask import request

app = Flask(__name__)
store = Store('plaid_codes.json')


def add_bank_transactions(
    bank,
    start_date="{:%Y-%m-%d}".format(datetime.datetime.now() +
                                    datetime.timedelta(days=-30)),
    end_date="{:%Y-%m-%d}".format(datetime.datetime.now()),
):
    transactions = get_transactions(store, bank, start_date, end_date)
    return add_transactions_to_coda(bank, transactions)


def update_bank_transactions(bank):
    # bankCodaId = store.get_bank(bank).row_id or bank
    bankCodaId = bank
    start_date = get_last_transaction_date_for_bank(bankCodaId)
    return add_bank_transactions(bank, start_date=start_date)


@app.route("/add_bank_transactions", methods=["POST"])
def add_bank_transactions_handler():
    bank = request.args.get("bank")
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    if bank is None:
        return "Bank not provided!", 400
    return add_bank_transactions(bank, start_date, end_date)
