

# Request for block validation (node broadcasting a block) - block_dict model
from typing import List, Optional

from pydantic import BaseModel


class BlockValidationRequest(BaseModel):
    previous_block_hash_hex: str            # bytes decoded to str
    transaction_hash_hex_list: List[str]    # list of bytes decoded to str
    validator_public_key_hex: str           # bytes decoded to str
    timestamp: float                        # unix timestamp float
    signature_hex: Optional[str]            # bytes decoded to str
    block_hash_hex: str                     # bytes decoded to str
    transaction_dict_list: List[dict]

    origin: str                             # address of origin
