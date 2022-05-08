from typing import Any, Optional, List

from pydantic import BaseModel

from transaction.transaction_type import TransactionType, TransactionContentType


# Request for block validation (node broadcasting a block) - block_dict model
class BlockValidationRequest(BaseModel):
    previous_block_hash_hex: str            # bytes decoded to str
    transaction_hash_hex_list: List[str]    # list of bytes decoded to str
    validator_public_key_hex: str           # bytes decoded to str
    timestamp: float                        # unix timestamp float
    signature_hex: Optional[str]            # bytes decoded to str
    block_hash_hex: str                     # bytes decoded to str
    transaction_dict_list: List[dict]

    origin: str                             # address of origin


class TransactionValidationRequest(BaseModel):
    source_public_key_hex: Optional[str]            # bytes decoded to str
    transaction_type: TransactionType               # int
    content_type: Optional[TransactionContentType]  # int
    content_hash_hex: Optional[str]                 # bytes decoded to str
    tx_fee: Optional[float]                         # float
    target_transaction_hash_hex: Optional[str]      # bytes decoded to str
    target_public_key_hex: Optional[str]            # bytes decoded to str
    tx_token: Optional[float]                       # float
    tx_object: Optional[Any]                        # any type (not decided)
    signature_hex: Optional[str]                    # bytes decoded to str
    transaction_hash_hex: str                       # bytes decoded to str
    timestamp: float                                # unix timestamp float

    origin: str                                     # address of origin


class NodeAddress(BaseModel):
    address: str


class ValidatorRandRequest(BaseModel):
    validator_public_key_hex: str  # bytes decoded to str
    rand: int                      # random number submitted by a validator
    previous_block_hash_hex: str   # previous block hash hex decoded to str
    timestamp: float               # timestamp of when the rand num is generated
    signature_hex: Optional[str]   # signature signed by the validator
