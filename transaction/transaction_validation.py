from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transaction.transaction import Transaction

from datetime import datetime
from account.account import Account
from transaction.transaction_exception import TransactionValidationError,\
    TransactionStakeError, TransactionTransferError, TransactionPayError
from transaction.transaction_type import TransactionType


class TransactionValidation:
    def __init__(self, transaction: Transaction, account: Account):
        self.transaction = transaction
        self.account = account

    def _validate_stake(self):
        if self.transaction.transaction_target.tx_token > self.account.balance:
            raise TransactionStakeError(self.transaction)

    def _validate_transfer(self):
        tx_amount = self.transaction.transaction_target.tx_token
        tx_fee = self.transaction.transaction_source.tx_fee
        if tx_amount + tx_fee > self.account.balance:
            raise TransactionTransferError(self.transaction)

    def _validate_tip(self):
        tx_amount = self.transaction.transaction_target.tx_token
        tx_fee = self.transaction.transaction_source.tx_fee
        if tx_amount + tx_fee > self.account.balance:
            raise TransactionPayError(self.transaction)

    def run(self):
        # general transaction validation
        if self.transaction.timestamp > datetime.utcnow():
            raise TransactionValidationError(
                message="Timestamp in future")
        if self.transaction.transaction_source.tx_fee < 0:
            raise TransactionValidationError(
                message="Negative transaction fee"
            )

        # transaction type based validation
        tx_type = self.transaction.transaction_source.transaction_type
        if tx_type == TransactionType.STAKE:
            self._validate_stake()
        elif tx_type == TransactionType.TRANSFER:
            self._validate_stake()
        elif tx_type == TransactionType.TIP:
            self._validate_tip()
