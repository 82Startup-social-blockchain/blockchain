from typing import List, Optional

from block.block import Block, create_block_from_dict
from utils import constants


# Blockchain is stored in RAM (at least for now)

class Blockchain:
    def __init__(self, head: Optional[Block] = None):
        # self.file_path = constants.BLOCKCHAIN_STORAGE_FILE_PATH
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

    def from_dict_list(self, blockchain_dict_list: List[dict]) -> Block:
        # convert list of blocks (blockes represented as dict) in JSON serializable format
        # to block list (list of Block objects) - used for converting received to this data structure
        # head is at index0
        previous_block, current_block = None, None
        for block_dict in reversed(blockchain_dict_list):
            current_block = create_block_from_dict(block_dict)
            current_block.previous_block = previous_block
            previous_block = current_block
        return current_block

    # TODO: add utility function for blockchain e.g. finding specific transaction in the blocks of the chain
