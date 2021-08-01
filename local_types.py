class Transaction:
    transaction_id: int
    date: str  # formatted as %Y-%m-%d
    amount: int  # amount in USD dollars
    name: str
    category: str
    city: str
    country: str

    def __init__(
        self, transaction_id, date, amount, name, category=None, city=None, country=None
    ):
        self.transaction_id = transaction_id
        self.date = date
        self.amount = amount
        self.name = name
        self.category = category
        self.city = city
        self.country = country
