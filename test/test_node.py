
import binascii
import json
from block.blockchain import Blockchain
from node.node import Node


class TestNode(Node):
    def __init__(self, blockchain: Blockchain):
        self.account_dict = dict()
        self.blockchain = blockchain
        self._initialize_accounts()

    def _to_dict(self):
        return {
            "blockchain_head_hex": binascii.hexlify(self.blockchain.head.block_hash).decode('utf-8'),
            "account_dict": {key_hex.decode('utf-8'): str(account) for key_hex, account in self.account_dict.items()}
        }

    def __str__(self):
        return json.dumps(self._to_dict())
