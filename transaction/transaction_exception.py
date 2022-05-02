from __future__ import annotations
import binascii
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from transaction.transaction import Transaction


class TransactionValidationError(Exception):
    def __init__(self, transaction: Transaction, message=""):
        base_message = f"(transaction: {binascii.hexlify(transaction.transaction_hash)})"
        if message != "":
            error_message = f"{message} {base_message}"
        else:
            error_message = base_message
        super().__init__(error_message)


class TransactionAccountError(TransactionValidationError):
    def __init__(
        self,
        transaction: Transaction,
        message=""
    ):
        super().__init__(transaction, message=f"[TransactionAccountError] {message}")


class TransactionStakeError(TransactionValidationError):
    def __init__(
        self,
        transaction: Transaction,
        message=""
    ):
        super().__init__(transaction, message=f"[TransactionStakeError] {message}")


class TransactionTransferError(TransactionValidationError):
    def __init__(
        self,
        transaction: Transaction,
        message=""
    ):
        super().__init__(transaction, message=f"[TransactionTransferError] {message}")


class TransactionTipError(TransactionValidationError):
    def __init__(
        self,
        transaction: Transaction,
        message=""
    ):
        super().__init__(transaction, message=f"[TransactionTipError] {message}")


class TransactionIcoError(TransactionValidationError):
    def __init__(
        self,
        transaction: Transaction,
        message=""
    ):
        super().__init__(transaction, message=f"[TransactionIcoError] {message}")


# TODO: Move this to block exception
class TransactionRewardError(TransactionValidationError):
    def __init__(
        self,
        transaction: Transaction,
        message="Invalid validator reward"
    ):
        super().__init__(transaction, message=message)
