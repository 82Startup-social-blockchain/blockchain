from typing import Optional, List

from pydantic import BaseModel

from transaction.transaction_type import TransactionType, TransactionContentType


# Request for block validation (node broadcasting a block) - block_dict model
class BlockValidationRequest(BaseModel):
    previous_block_hash_hex: Optional[str]  # bytes decoded to str
    transaction_hash_hex_list: List[str]    # list of bytes decoded to str
    validator_public_key_hex: str           # bytes decoded to str
    timestamp: str                          # datetime in isoformat
    signature_hex: str                      # bytes decoded to str
    block_hash_hex: str                     # bytes decoded to str
    transaction_dict_list: List[dict]


class TransactionRequest(BaseModel):
    # parent transaction or the recipient
    # target_transaction_hash: Optional[str]
    # target_public_key: Optional[str]

    # amount: Optional[float]

    # public_key: str

    # content_type: Optional[TransactionContentType]
    # content: Optional[str]  # react does not have content
    pass


class NodeAddress(BaseModel):
    address: str
