import json
from typing import Dict


class Bank:
    def __init__(self, item_id, access_code, row_id) -> None:
        self.item_id = item_id
        self.access_code = access_code
        self.row_id = row_id


class Store:
    data: Dict[str, Bank]

    def __init__(self, file_name) -> None:
        with open(file_name) as f:
            raw_data = json.load(f)
        self.data = {}
        for item, props in raw_data.items():
            item_id, access_code, row_id = props.values()
            self.data[item] = Bank(item_id, access_code, row_id)

    def get_bank(self, item) -> Bank:
        return self.data[item]

    def get_access_code_from_name(self, item_name: str) -> str:
        return self.data[item_name].access_code

    def get_banks(self):
        return set(self.data.keys())
