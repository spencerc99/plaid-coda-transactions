# Setup
## Accounts Prerequisite
### 1) Register for a developer Plaid account
Head to the website to register for a Plaid developer account. It might takes a few days to get approved.
Once you have your developer key, come back here and set up an `.env` file that looks like:
```
PLAID_CLIENT_ID=<number like 123456789>
PLAID_SECRET=<number like 123456789>
PLAID_PUBLIC_KEY=<number like 123456789>
PLAID_ENV=development
PLAID_PRODUCTS=transactions
PLAID_COUNTRY_CODES=US
```

You might need to request access to more accounts (I believe there's a limit of 5 by default) from customer support if you have more than that limit of accounts you want to sync from.



### 2) Register for a Coda account if you don't have one
Head to coda.io to get setup with a new account. You'll need to head to your Account Settings (click your profile picture in the top right) to get a developer API key
* [ ] add gif for doing this

1. Once you have your API key, augment your `.env` file with the following
```
...
PLAID_COUNTRY_CODES=US
CODA_API_KEY=<code like blah-blah-blah>
```

2. Copy this template that I've created for this and find the following tables in this page
* [ ] add gif for this

## Setting up this app

### Setting up your banks in Coda
Head to this page in your new Coda template and add a row for each bank you want to grab transactions from. 

* [ ] add automated syncing of fresh rows and modifying plaid_codes.json by matching on name

### Run the Plaid server to get your codes

install all the required dependencies using your favorite python version/package manager from `requirements.txt`. A simple setup is the following
```
pip install -r requirements.txt
```

Now you can run the following to spin up the sample Plaid server
```
python server.py
```

Navigate to localhost:5000 in your browser to see the sample Plaid interface. From there, you can sign into the various credit card accounts that you want to sync transactions from.

After you sign in with each one, make sure to grab the item ID and accessCode that should be displayed at the top and fill it in in a new file called `plaid_codes.json` with the following format. You can choose whatever string identifier for the bank names and fill out the respective item IDs and access codes. Fill in the `codaRowId` from the previous Coda page using the "Row ID" column in the table and matching it with the respective bank.
```
{
  "Discover": {
    "itemId": "<big string code>",
    "accessCode": "access-development-<big string code>",
    "codaRowId": 1
  },
  "Chase": {
    "itemId": "<big string code>",
    "accessCode": "access-development-<big string code>",
    "codaRowId": "r2"
  },
  "Fidelity": {
    "itemId": "<big string code>",
    "accessCode": "access-development-<big string code>",
    "codaRowId": 3
  },
  "Barclays": {
    "itemId": "<big string code>",
    "accessCode": "access-development-<big string code>",
    "codaRowId": 9
  },
  "BoFA": {
    "itemId": "<big string code>",
    "accessCode": "access-development-<big string code>",
    "codaRowId": 10
  }
}
```

* [ ] automate this by setting up free cron job on AWS
* [ ] 

## Usage
You should be all set at this point! You can run the following to sync your transactions into Coda (run main.py with a list of the bank names corresponding to the ones you want to pull from in `plaid_codes.json`)
```
python main.py <bank1> <bank2> ...
```
