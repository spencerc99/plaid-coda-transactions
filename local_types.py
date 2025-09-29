from dataclasses import dataclass
from typing import List

@dataclass
class Transaction:
    amount: float
    category: List[str]
    name: str
    datetime: str  # Full datetime in ISO format (YYYY-MM-DDTHH:mm:ssZ) for proper ordering
    date: str  # Keep for backward compatibility (YYYY-MM-DD)
    transaction_id: str
    city: str
    country: str

    def __init__(
        self, transaction_id, amount, name, datetime=None, date=None, category=None, city=None, country=None
    ):
        self.transaction_id = transaction_id
        self.datetime = datetime
        self.date = date
        self.amount = amount
        self.name = name
        self.category = category
        self.city = city
        self.country = country
