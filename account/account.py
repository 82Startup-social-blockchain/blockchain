import json
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ec


# public account class that is used for actual code
class Account:
    def __init__(
        self,
        public_key_hex: bytes
    ):
        self.public_key_hex = public_key_hex
        self.stake = 0  # amount of tokens staked
        self.balance = 0  # amount of tokens account possesses

    def __str__(self):
        return json.dumps(self.to_dict())

    def to_dict(self):
        return {
            "public_key_hex": self.public_key_hex.decode('utf-8'),
            "stake": self.stake,
            "balance": self.balance
        }
