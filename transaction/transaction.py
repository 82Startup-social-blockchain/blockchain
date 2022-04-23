import datetime
from typing import Optional

from transaction_type import TransactionType, TransactionContentType


class TransactionSource:
    def __init__(
        self,
        source_public_key: str,  # public key of the content creator
        transaction_type: TransactionType,
        content_type: Optional[TransactionContentType] = None,
        content_hash: Optional[str] = None,
    ):
        self.source_public_key = source_public_key
        self.transaction_type = transaction_type
        self.content_type = content_type

        # content is required to make sure that content is not manipulated by nodes
        self.content_hash = content_hash


class TransactionTarget:
    def __init__(
        self,
        target_transaction_hash: Optional[str] = None,
        target_public_key: Optional[str] = None,
        amount: Optional[float] = None
    ):
        self.target_transaction_hash = target_transaction_hash
        self.target_publick_key = target_public_key
        self.amount = amount


class Transaction:
    # Transaction object is the object being stored in blocks
    def __init__(
        self,
        transaction_source: TransactionSource,
        transaction_target: TransactionTarget
    ):
        self.transaction_source = transaction_source
        self.transaction_target = transaction_target

        self.timestamp = datetime.datetime.now(datetime.timezone.utc)

        # used as key of the external database
        self.transaction_hash = self.get_transaction_hash()

        # sign the transaction using
        self.signature = None

    def get_transaction_hash(self):
        pass

    def sign_transaction(self, account):
        # self.signature =
        pass


class TransactionWithContent:
    # TransactionWithContent object is being broadcasted to other nodes
    def __init__(
        self,
        transaction: Transaction,
        content: str
    ):
        self.transaction = transaction
        self.content = content
