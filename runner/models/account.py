from pydantic import BaseModel


class Account(BaseModel):
    public_key_hex: str  # bytes decoded to str
    stake: float
    balance: float
