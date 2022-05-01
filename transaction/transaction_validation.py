from __future__ import annotations
import json
from typing import TYPE_CHECKING, Optional

from utils.constants import ICO_PUBLIC_KEY_FILE, ICO_TOKENS

if TYPE_CHECKING:
    from transaction.transaction import Transaction

from datetime import datetime
from account.account import Account
from transaction.transaction_exception import TransactionIcoError, TransactionValidationError,\
    TransactionStakeError, TransactionTransferError, TransactionTipError
from transaction.transaction_type import TransactionType
from utils.crypto import get_public_key_hex


class TransactionValidation:
    def __init__(self, transaction: Transaction, account: Optional[Account]):
        self.transaction = transaction
        self.account = account

    def _validate_stake(self):
        if self.transaction.transaction_target.tx_token > self.account.balance:
            raise TransactionStakeError(self.transaction)

    def _validate_transfer(self):
        if self.account is None:
            raise TransactionValidationError(self.transaction, message="Account does not exist")

        tx_token = self.transaction.transaction_target.tx_token
        if tx_token is None:
            raise TransactionTransferError(self.transaction, message="Transfer token amount null")

        tx_fee = self.transaction.transaction_source.tx_fee
        if tx_fee is not None and tx_token + tx_fee > self.account.balance:
            raise TransactionTransferError(self.transaction)

    def _validate_tip(self):
        if self.account is None:
            raise TransactionValidationError(self.transaction, message="Account does not exist")

        tx_token = self.transaction.transaction_target.tx_token
        if tx_token is None:
            raise TransactionTipError(self.transaction, message="Transfer token amount null")

        tx_fee = self.transaction.transaction_source.tx_fee
        if tx_fee is not None and tx_token + tx_fee > self.account.balance:
            raise TransactionTipError(self.transaction)

    def _validate_ico(self):
        with open(ICO_PUBLIC_KEY_FILE, 'r') as fp:
            ico_accounts = list(map(lambda x: x.encode('utf-8'), json.load(fp)))

        # validate if transaction account is in ICO list
        if self.transaction.transaction_source.source_public_key_hex not in ico_accounts:
            raise TransactionIcoError(self.transaction)

        # validate if transaction account is in ICO list
        if self.transaction.transaction_target.tx_token != ICO_TOKENS:
            raise TransactionIcoError(self.transaction, message="ICO token amount invalid")

    def run(self):
        # general transaction validation
        if self.transaction.timestamp > datetime.utcnow():
            raise TransactionValidationError(self.transaction, message="Timestamp in future")

        tx_fee = self.transaction.transaction_source.tx_fee
        if tx_fee is not None and tx_fee < 0:
            raise TransactionValidationError(self.transaction, message="Negative transaction fee")

        # transaction type based validation
        tx_type = self.transaction.transaction_source.transaction_type
        if tx_type == TransactionType.STAKE:
            self._validate_stake()
        elif tx_type == TransactionType.TRANSFER:
            self._validate_stake()
        elif tx_type == TransactionType.TIP:
            self._validate_tip()
        elif tx_type == TransactionType.ICO:
            self._validate_ico()
