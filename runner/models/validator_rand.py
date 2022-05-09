from typing import Optional

from pydantic import BaseModel


class ValidatorRandRequest(BaseModel):
    validator_public_key_hex: str  # bytes decoded to str
    rand: int                      # random number submitted by a validator
    previous_block_hash_hex: str   # previous block hash hex decoded to str
    timestamp: float               # timestamp of when the rand num is generated
    signature_hex: Optional[str]   # signature signed by the validator
