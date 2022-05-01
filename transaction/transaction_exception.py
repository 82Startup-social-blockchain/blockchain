from __future__ import annotations
import binascii
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transaction.transaction import Transaction


class TransactionValidationError(Exception):
    def __init__(self, transaction: Transaction, message=""):
        base_message = f"Illegal transaction {binascii.hexlify(transaction.transaction_hash)}"
        if message != "":
            error_message = f"{base_message} - {message}"
        else:
            error_message = base_message
        super().__init__(error_message)


class TransactionStakeError(TransactionValidationError):
    def __init__(
        self,
        transaction: Transaction,
        message="Stake amount higher than balance"
    ):
        super().__init__(transaction, message=message)


class TransactionTransferError(TransactionValidationError):
    def __init__(
        self,
        transaction: Transaction,
        message="Transfer amount higher than balance"
    ):
        super().__init__(transaction, message=message)


class TransactionTipError(TransactionValidationError):
    def __init__(
        self,
        transaction: Transaction,
        message="Tip amount higher than balance"
    ):
        super().__init__(transaction, message=message)


class TransactionIcoError(TransactionValidationError):
    def __init__(
        self,
        transaction: Transaction,
        message="Invalid account for ICO"
    ):
        super().__init__(transaction, message=message)
