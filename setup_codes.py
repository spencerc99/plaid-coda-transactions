"""
This file runs a script to help set this project to be properly hooked up with Coda by prompting for the necessary inputs.
"""
import urllib.parse
import requests
import click
import os
import dotenv
import json

DOT_ENV_PATH = ".env"
transaction_table_name = "Transactions"
transaction_column_names = [
    "Amount (paid)",
    "Automatic Category",
    "Description",
    "Date",
    "Transaction ID",
    "City",
    "Country",
    "Source",
]

# mapping of plaid names to the column names above
plaid_properties_to_transaction_column_names = {
    "amount": "Amount (paid)",
    "category": "Automatic Category",
    "name": "Description",
    "date": "Date",
    "transaction_id": "Transaction ID",
    "city": "City",
    "country": "Country",
}

bank_table_name = "Transaction Sources"
bank_column_names = ["Last Transaction Date", "last transaction id"]


@click.command()
@click.option(
    "--plaid_client_id",
    prompt="Plaid Client ID",
    help="Plaid Developer Client ID (see https://dashboard.plaid.com/overview/development)",
)
@click.option(
    "--plaid_secret",
    prompt="Plaid Secret",
    help="Plaid Developer Secret (see https://dashboard.plaid.com/overview/development)",
)
@click.option(
    "--plaid_public_key",
    prompt="Plaid Public Key",
    help="Plaid Developer Public Key (see https://dashboard.plaid.com/overview/development)",
)
@click.option(
    "--coda_api_key",
    prompt="Coda API Key",
    help="API Key for Coda (see https://coda.io/developers/apis/v1#section/Using-the-API/Resource-IDs-and-Links)",
)
@click.option(
    "--doc_id",
    prompt="Coda Doc ID",
    help="Doc ID from Coda (see https://coda.io/developers/apis/v1#section/Using-the-API/Resource-IDs-and-Links for help)",
)
@click.option(
    "--doc_id",
    prompt="Coda Doc ID",
    help="Doc ID from Coda (see https://coda.io/developers/apis/v1#section/Using-the-API/Resource-IDs-and-Links for help)",
)
def set_environment_info(
    plaid_client_id, plaid_secret, plaid_public_key, coda_api_key, doc_id
):
    dotenv.set_key(DOT_ENV_PATH, "PLAID_CLIENT_ID", plaid_client_id)
    dotenv.set_key(DOT_ENV_PATH, "PLAID_SECRET", plaid_secret)
    dotenv.set_key(DOT_ENV_PATH, "PLAID_PUBLIC_KEY", plaid_public_key)
    dotenv.set_key(DOT_ENV_PATH, "CODA_API_KEY", coda_api_key)

    ### prompt user for doc id
    dotenv.set_key(DOT_ENV_PATH, "CODA_DOC_ID", doc_id)
    headers = {"Authorization": f"Bearer {coda_api_key}"}
    click.echo("Information saved. Retrieving table information from Coda...")
    click.echo(f"Looking for the `{transaction_table_name}` table")
    response = requests.get(
        f"https://coda.io/apis/v1/docs/{doc_id}/tables/{transaction_table_name}",
        headers=headers,
    )
    response.raise_for_status()
    table_info = json.loads(response.text)
    transactions_table_id = table_info.id
    dotenv.set_key(DOT_ENV_PATH, "CODA_TRANSACTIONS_TABLE_ID", transactions_table_id)

    click.echo(
        f"Found `{transactions_table_id}` as the ID for the `{transaction_table_name}` table."
    )

    response = requests.get(
        f"https://coda.io/apis/v1/docs/{doc_id}/tables/{transactions_table_id}/columns",
        headers=headers,
    )
    response.raise_for_status()
    transaction_column_infos = json.loads(response.text)
    for col_name in transaction_column_names:
        col_info, *_ = [
            col for col in transaction_column_infos.items if col_name == col.name
        ]
        # TODO: make json file instead of .env?
        dotenv.set_key() col_info.id

    click.echo(
        f"Found `{transactions_table_id}` as the ID for the `{transaction_table_name}` table."
    )

    ### to encode column names: urllib.parse.quote(...)
    ### grab necessary transaction grid + column ids
    # CODA_TRANSACTIONS_TABLE_ID
    # CODA_TRANSACTIONS_TABLE_SOURCE_COL_ID

    ### grab necessary bank grid + column ids
    # CODA_LAST_TRANSACTION_DATE_COL_ID
    # CODA_LAST_TRANSACTION_ID_COL_ID
    # CODA_BANK_TABLE_ID


# print out .env file at end


if __name__ == "__main__":
    handle_file_setup()
    if not os.path.exists(DOT_ENV_PATH):
        # create the .env file
        with open(DOT_ENV_PATH, "w"):
            pass
    else:
        click.echo(f"`{DOT_ENV_PATH}` path already exists.")
        shouldOverride = click.prompt(
            "Do you wish to proceed and override the content there?"
        )
        if not shouldOverride:
            return
    set_environment_info()
