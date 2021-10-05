from enum import Enum
from local_types import Transaction
from typing import List
from venmo_api import Client
import os, sys
import datetime


# Get your access token. You will need to complete the 2FA process
def setup_access_token(username, password):
    access_token = Client.get_access_token(username=username, password=password)
    print(f"Your access token is {access_token}")
    client = Client(access_token=access_token)
    user = client.user.get_user_by_username(username=username)
    if not user:
        print(
            "Your profile is private, so you'll need to manually find it on the venmo website. Look for `external_id` in the query param of the API on your profile page on the venmo desktop website."
        )
    else:
        print(f"Your user id is {user.id}")


VENMO_ACCESS_TOKEN = os.getenv("VENMO_ACCESS_TOKEN")
if VENMO_ACCESS_TOKEN:
    venmo = Client(access_token=VENMO_ACCESS_TOKEN)
VENMO_USER_ID = os.getenv("VENMO_USER_ID")


class PaymentType(Enum):
    Charge = "charge"
    Pay = "pay"


class VenmoTransaction:
    id: int
    date_created: int
    amount: int
    note: str
    payment_type: PaymentType


def transform_transaction_amount_sign(t: VenmoTransaction) -> int:
    """
    Returns the appropriate transformed amount (positive or negative) for the given
    transaction according to the payment type and whether the actor matches me.

    returns negative if it qualifies as income and
    positive if it qualifies as a payment to match
    the Plaid scheme of other transactions
    """
    abs_amount = abs(t.amount)
    is_target_same_user = t.target.id == VENMO_USER_ID
    is_income = (
        t.payment_type == PaymentType.Charge.value and not is_target_same_user
    ) or (t.payment_type == PaymentType.Pay.value and is_target_same_user)
    return -abs_amount if is_income else abs_amount


def get_transactions(last_transaction_id, start_transaction_ts) -> List[Transaction]:
    # paginated grab transactions until encountering last transction id or last transaction date inclusive
    if not venmo:
        print("Venmo client not set up! Skipping Venmo transactions.")
        return
    transactions: List[VenmoTransaction] = venmo.user.get_user_transactions(
        user_id=VENMO_USER_ID
    )
    
    transactions_to_add = []
    while transactions:
        for transaction in transactions:
            if last_transaction_id:
                if transaction.id == last_transaction_id:
                    break
            if start_transaction_ts:
                if transaction.date_created < start_transaction_ts:
                    break
            transactions_to_add.append(
                Transaction(
                    amount=transform_transaction_amount_sign(transaction),
                    transaction_id=transaction.id,
                    date="{:%Y-%m-%d}".format(
                        datetime.datetime.fromtimestamp(transaction.date_created)
                    ),
                    name=transaction.note,
                )
            )
        transactions = transactions.get_next_page()

    return transactions_to_add


if __name__ == "__main__":
    # setup venmo code if not there
    [_, username, password] = sys.argv
    setup_access_token(username, password)
