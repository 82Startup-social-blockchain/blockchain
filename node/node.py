import binascii
import json
import logging
import httpx

import requests

from block.block import Block
from block.blockchain import Blockchain
from transaction.transaction import Transaction
from utils import constants


logger = logging.getLogger(__name__)


class Node:
    def __init__(self, address: str):
        self.address = address
        self.known_node_address_set = self._initialize_known_node_address_set()
        self.blockchain = None

        self.transaction_pool = dict()  # { transaction_hash_hex: Transaction }
        self.transaction_broadcasted = dict()  # { transactino_hash_hex: set }

    def _initialize_known_node_address_set(self):
        # TODO: use something better than just json

        # Initialize known nodes list from seed_node_address_list
        with open(constants.SEED_NODES_FILE, 'r') as fp:
            address_set = set(json.load(fp))
        return address_set

    def _request_addresses_from_known_nodes(self):
        # Request node addresses from known nodes
        added_address_set = set([])
        disconnected_address_set = set([])
        for address in self.known_node_address_set:
            if address == self.address:
                continue
            url = address + constants.KNOWN_NODES_PATH
            try:
                r = requests.get(url=url)
                added_address_set.update(set(r.json()))
            except requests.exceptions.ConnectionError:
                disconnected_address_set.add(address)

        self.known_node_address_set.update(added_address_set)
        self.known_node_address_set.discard(self.address)
        self.known_node_address_set.difference_update(disconnected_address_set)

    def _advertise_to_known_nodes(self):
        # Advertise itself to known nodes so that those nodes have this node in their known node list
        disconnected_address_set = set([])
        for address in self.known_node_address_set:
            if address == self.address:
                continue
            url = address + constants.NODE_REQUEST_PATH
            data = {"address": self.address}
            headers = {"Content-Type": "application/json"}
            try:
                requests.post(url=url, json=data, headers=headers)
                logger.info(f"Advertised to node {address}")
            except requests.exceptions.ConnectionError:
                disconnected_address_set.add(address)

        self.known_node_address_set.difference_update(disconnected_address_set)

    def _get_longest_blockchain(self):
        disconnected_address_set = set([])
        for address in self.known_node_address_set:
            if address == self.address:
                continue
            url = address + constants.BLOCKCHAIN_REQUEST_PATH
            try:
                r = requests.get(url=url)
                if self.blockchain is None:
                    self.blockchain = Blockchain()
                    self.blockchain.from_dict_list(r.json())
                else:
                    # TODO: update after head instead of re-initializing
                    if len(self.blockchain.head) < len(r.json()):
                        self.blockchain.from_dict_list(r.json())
            except requests.exceptions.ConnectionError:
                disconnected_address_set.add(address)
        self.known_node_address_set.difference_update(disconnected_address_set)

    def accept_new_node(self, address: str):
        logger.info(f"Accepted node {address}")
        self.known_node_address_set.add(address)

    def join_network(self):
        # 1. Ask seed nodes for their known nodes
        self._request_addresses_from_known_nodes()

        # 2. Advertise itself to known nodes
        self._advertise_to_known_nodes()

        # 3. get blockchain from known nodes
        self._get_longest_blockchain()

    async def accept_new_transaction(self, transaction: Transaction, origin: str):
        # TODO: use thread lock because same transaction may come in at the same time

        transaction_hash_hex = binascii.hexlify(
            transaction.transaction_hash)
        logger.info(
            f"Received transaction {transaction_hash_hex} from {origin}")

        # 1. Check if transaction in transaction pool
        if transaction.transaction_hash in self.transaction_pool:
            return None

        # 2. Validate transaction
        transaction.validate()

        # 3. Add to transaction pool
        self.transaction_pool[transaction_hash_hex] = transaction

        # 4. Broadcast to other nodes
        await self._broadcast_transaction(transaction, origin)

        # 5. TODO: Add block to blockchain if the condition is met

    async def _broadcast_transaction(self, transaction: Transaction, origin: str):
        transaction_hash_hex = binascii.hexlify(
            transaction.transaction_hash)

        # add transaction to broadcasted set
        if transaction_hash_hex not in self.transaction_broadcasted:
            self.transaction_broadcasted[transaction_hash_hex] = set([])

        disconnected_address_set = set([])
        for address in self.known_node_address_set:
            if address == origin or address in self.transaction_broadcasted[transaction_hash_hex]:
                continue
            url = address + constants.TRANSACTION_VALIDATION_PATH
            headers = {"Content-type": "application/json"}
            data = transaction.to_dict()
            data["origin"] = self.address
            try:
                self.transaction_broadcasted[transaction_hash_hex].add(
                    address)
                # requests.post(url=url, headers=headers, json=data)
                async with httpx.AsyncClient() as client:
                    await client.post(url, headers=headers, json=data)
                logger.info(
                    f'Broadcasted transaction {transaction_hash_hex} to {address}')
            except requests.exceptions.ConnectionError:
                disconnected_address_set.add(address)

        self.known_node_address_set.difference_update(
            disconnected_address_set)

    def accept_new_block(self, block: Block, origin: str):
        # TODO: use thread lock because same block may come in at the same time

        # 1. Validate block
        block.validate()

        # 2. Add block to blockchain - TODO: change mechanism with POS
        self.blockchain.add_new_block(block)

        # 3. TODO: remove transactions from transaction pool

        # 4. Broadcast
