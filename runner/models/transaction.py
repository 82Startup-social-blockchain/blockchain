from typing import Any, Optional

from pydantic import BaseModel

from transaction.transaction_type import TransactionType, TransactionContentType


class Transaction(BaseModel):
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


class TransactionValidationRequest(Transaction):
    origin: str                                     # address of origin


class TransactionCreateRequest(BaseModel):
    private_key_hex: str                            # bytes decoded to str
    transaction_type: TransactionType               # int
    content_type: Optional[TransactionContentType]  # int
    content: Optional[str]                          # any data - only support str for now
    target_transaction_hash_hex: Optional[str]      # bytes decoded to str
    target_public_key_hex: Optional[str]            # bytes decoded to str
    tx_token: Optional[float]
    tx_object: Optional[Any]
    tx_fee: Optional[float]

    encryption_key: Optional[str]                   # key to encrypt content before uploading it to storage
