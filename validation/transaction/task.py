from __future__ import annotations
import json
import time
from tkinter import N
from typing import TYPE_CHECKING, Optional

from account.account import Account
from validation.transaction.exception import TransactionAccountError, TransactionIcoError, \
    TransactionValidationError, TransactionStakeError, TransactionTransferError, TransactionTipError
from transaction.transaction_type import TransactionType
from utils.constants import ICO_PUBLIC_KEY_FILE, ICO_TOKENS, VALIDATION_REWARD

if TYPE_CHECKING:
    from transaction.transaction import Transaction


class TransactionValidationTask:
    def __init__(
        self,
        transaction: Transaction,
        account: Optional[Account],
        is_initial_block: bool = False
    ):
        self.transaction = transaction
        self.account = account
        self.is_initial_block = is_initial_block

    def _validate_stake(self):
        if self.account is None:
            raise TransactionAccountError(self.transaction, message="Account nonexistent")

        if self.transaction.transaction_target.tx_token is None:
            raise TransactionStakeError(self.transaction, message="Stake token amount null")

        if self.transaction.transaction_target.tx_token > self.account.balance:
            raise TransactionStakeError(self.transaction, message="Stake amount higher than balance")

        if not float(self.transaction.transaction_target.tx_token).is_integer():
            raise TransactionStakeError(self.transaction, message="Stake token amount not an integer")

    def _validate_transfer(self):
        if self.account is None:
            raise TransactionAccountError(self.transaction, message="Account nonexistent")

        tx_token = self.transaction.transaction_target.tx_token
        if tx_token is None:
            raise TransactionTransferError(self.transaction, message="Transfer token amount null")
        if tx_token < 0:
            raise TransactionTransferError(self.transaction, message="Transfer token amount negative")

        if self.transaction.transaction_source.tx_fee is not None:
            tx_fee = self.transaction.transaction_source.tx_fee
        else:
            tx_fee = 0
        if tx_token + tx_fee > self.account.balance:
            raise TransactionTransferError(
                self.transaction,
                message=f"Transfer token amount (${tx_token}) higher than balance (${self.account.balance})"
            )

        if self.transaction.transaction_target.target_public_key_hex is None:
            raise TransactionTransferError(self.transaction, message="Transfer target null")

    def _validate_tip(self):
        if self.account is None:
            raise TransactionAccountError(self.transaction, message="Account nonexistent")

        tx_token = self.transaction.transaction_target.tx_token
        if tx_token is None:
            raise TransactionTipError(self.transaction, message="Tip token amount null")
        if tx_token < 0:
            raise TransactionTipError(self.transaction, message="Tip token amount negative")

        if self.transaction.transaction_source.tx_fee is not None:
            tx_fee = self.transaction.transaction_source.tx_fee
        else:
            tx_fee = 0
        if tx_token + tx_fee > self.account.balance:
            raise TransactionTipError(
                self.transaction,
                message=f"Tip amount (${tx_token}) higher than balance (${self.account.balance})"
            )

        if self.transaction.transaction_target.target_public_key_hex is None:
            raise TransactionTipError(self.transaction, message="Tip target null")

    def _validate_ico(self):
        with open(ICO_PUBLIC_KEY_FILE, 'r') as fp:
            ico_accounts = list(map(lambda x: x.encode('utf-8'), json.load(fp)))

        # validate that it is not the initial block
        if not self.is_initial_block:
            raise TransactionIcoError(self.transaction, message=f"ICO transaction in non-initial block")

        # validate if transaction account is in ICO list
        ico_account = self.transaction.transaction_source.source_public_key_hex
        if ico_account not in ico_accounts:
            raise TransactionIcoError(self.transaction, message=f"Invalid ICO account {ico_account}")

        # validate if ico amount is valid
        if self.transaction.transaction_target.tx_token != ICO_TOKENS:
            raise TransactionIcoError(self.transaction, message="ICO token amount invalid")

    def run(self):
        # general transaction validation
        if self.transaction.timestamp > time.time():
            raise TransactionValidationError(self.transaction, message="Timestamp in future")

        tx_fee = self.transaction.transaction_source.tx_fee
        if tx_fee is not None and tx_fee < 0:
            raise TransactionValidationError(self.transaction, message="Negative transaction fee")

        # transaction type based validation
        tx_type = self.transaction.transaction_source.transaction_type
        if tx_type == TransactionType.STAKE:
            self._validate_stake()
        elif tx_type == TransactionType.TRANSFER:
            self._validate_transfer()
        elif tx_type == TransactionType.TIP:
            self._validate_tip()
        elif tx_type == TransactionType.ICO:
            self._validate_ico()
