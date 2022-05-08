from __future__ import annotations
import binascii
from typing import TYPE_CHECKING, Dict, Optional
from account.account import Account

from validation.block.exception import BlockPreviousBlockError, BlockValidationError, BlockValidatorError

if TYPE_CHECKING:
    from block.block import Block


class BlockValidationTask:
    def __init__(
        self, block: Block,
        account_dict: Optional[Dict[bytes, Account]],
        block_validator_dict: Optional[Dict[bytes, bytes]] = None
    ):
        self.block = block
        self.block_validator_dict = block_validator_dict
        self.account_dict = account_dict

    def _validate_transactions(self):
        for transaction in self.block.transaction_list:
            tx_publick_key_hex = transaction.transaction_source.source_public_key_hex
            transaction.validate(
                self.account_dict.get(tx_publick_key_hex, None),
                is_initial_block=self.block._is_initial_block()
            )

    def _validate_validator(self):
        if self.block.previous_block is not None:
            previous_block_hash_hex = binascii.hexlify(self.block.previous_block.block_hash)
        elif self.block.previous_block_hash_hex is not None:
            previous_block_hash_hex = self.block.previous_block_hash_hex
        else:
            raise BlockPreviousBlockError(self.block, message="Previous block hash hex nonexistent")

        if previous_block_hash_hex not in self.block_validator_dict:
            raise BlockValidatorError(self.block, message="No validator of the received block")
        if self.block_validator_dict[previous_block_hash_hex] != self.block.validator_public_key_hex:
            raise BlockValidatorError(self.block, message="Wrong validator of the received block")

    def run(self):
        self._validate_transactions()
        if self.block_validator_dict is not None:
            self._validate_validator()
