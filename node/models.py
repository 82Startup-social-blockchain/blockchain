from typing import Optional

from pydantic import BaseModel

from transaction.transaction_type import TransactionType, TransactionContentType


# Request that an account sends to node to upload activity data
class TransactionRequest(BaseModel):
    # parent transaction or the recipient
    target_transaction_hash: Optional[str]
    target_public_key: Optional[str]

    amount: Optional[float]

    public_key: str

    content_type: Optional[TransactionContentType]
    content: Optional[str]  # react does not have content
