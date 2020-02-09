import plaid
from dotenv import load_dotenv
import os

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


def get_transactions(store, item, start_date, end_date):
    """
    date must be formatted as follows: '{:%Y-%m-%d}'.format(datetime.datetime.now())
    """
    print(
        f'Getting transactions for {item} between {start_date} and {end_date}')
    access_token = store.get_bank(item).access_code
    try:
        transactions_resp = client.Transactions.get(
            access_token, start_date, end_date)
        return transactions_resp
    except plaid.errors.PlaidError as e:
        return format_error(e)
