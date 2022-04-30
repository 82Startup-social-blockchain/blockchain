from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ec


# public account class that is used for actual code
class Account:
    def __init__(
        self,
        public_key_hex: bytes
    ):
        self.public_key_hex = public_key_hex
        self.balance = 0  # amount of tokens account possesses
        self.stake = 0  # amount of tokens staked
