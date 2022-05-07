import binascii
import logging
from typing import Dict, List, Optional

from account.account import Account
from block.block import Block, create_block_from_dict
from block.block_exception import BlockNotHeadError
from transaction.transaction_type import TransactionType
from utils import constants


logger = logging.getLogger(__name__)


# Blockchain is stored in RAM (at least for now)

class Blockchain:
    def __init__(self, head: Optional[Block] = None):
        self.head = head

    def to_dict_list(self) -> List[dict]:
        # convert the whole chain to a list of blocks (blocks represented as dict)
        # convert the blockchain into a JSON serializable format - used for converting before sending
        blockchain_list = []  # head is at index 0
        current_block = self.head
        while current_block:
            blockchain_list.append(current_block.to_dict())
            current_block = current_block.previous_block
        return blockchain_list

    def from_dict_list(self, blockchain_dict_list: List[dict]):
        # convert list of blocks (blockes represented as dict) in JSON serializable format
        # to block list (list of Block objects) - used for converting received to this data structure
        # head is at index0
        previous_block, current_block = None, None
        for block_dict in reversed(blockchain_dict_list):
            current_block = create_block_from_dict(block_dict, previous_block)
            previous_block = current_block
        self.head = current_block

    def add_new_block(self, block: Block) -> None:
        # assume that input block is validated
        if block.previous_block is None and block.previous_block_hash_hex is not None:
            if self.head.block_hash != binascii.unhexlify(block.previous_block_hash_hex):
                raise BlockNotHeadError(
                    block, message="Requested block is not linked to the current head"
                )
            block.previous_block = self.head
        self.head = block

    def validate(self):
        # validate the whole blockchain from head to the initial block
        account_dict = {}
        block_dict_list = self.to_dict_list()
        previous_block = None
        for block_dict in reversed(block_dict_list):
            block = create_block_from_dict(block_dict, previous_block=previous_block)
            block.validate(account_dict)
            block.update_account_dict(account_dict)
            previous_block = block

    def initialize_accounts(self) -> Dict[bytes, Account]:
        # initialize Account dict - assume blockchain is valid
        # return { public key: Account object }
        if self.head is None:
            return {}

        account_dict = dict()
        block_dict_list = self.to_dict_list()
        previous_block = None
        for block_dict in reversed(block_dict_list):
            block = create_block_from_dict(block_dict, previous_block=previous_block)
            block.update_account_dict(account_dict)
            previous_block = block

        logger.info(f"Initialized {len(account_dict)} accounts")
        return account_dict

        # TODO: add functino to append blocks to head instead of re-initializing

        # TODO: add utility function for blockchain e.g. finding specific transaction in the blocks of the chain
