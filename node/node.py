import asyncio
import binascii
import json
import logging
import secrets
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import ec
import httpx
import requests

from block.block import Block
from block.blockchain import Blockchain
from transaction.transaction import Transaction
from utils import constants


logger = logging.getLogger(__name__)


class Node:
    def __init__(
        self,
        address: str,
        private_key: Optional[Optional[ec.EllipticCurvePrivateKey]] = None
    ):
        self.address = address
        self.private_key = private_key  # private key of this node - used for signing block, etc.
        self.known_node_address_set = self._initialize_known_node_address_set()
        self.blockchain = None

        self.transaction_pool = dict()  # { transaction_hash_hex: Transaction }
        self.transaction_broadcasted = dict()  # { transactino_hash_hex: set }
        self.block_broadcasted = dict()  # { block_hash_hex: set }

        self.account_dict = dict()  # { account_public_key_hex: Account }

        self.lock = asyncio.Lock()

    ##### Initialization functions #####

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
        origin_address = None
        for address in self.known_node_address_set:
            if address == self.address:
                continue
            url = address + constants.BLOCKCHAIN_REQUEST_PATH
            try:
                r = requests.get(url=url)
                if self.blockchain is None:
                    self.blockchain = Blockchain()
                    # if r.json() is empty list => blockchain has head None
                    self.blockchain.from_dict_list(r.json())
                    # validate blockchain
                    try:
                        self.blockchain.validate()
                        origin_address = address
                    except Exception as e:
                        logger.error(f"Error fetching longest chain: {e}")
                        self.blockchain = None
                else:
                    # TODO: update after head instead of re-initializing
                    if len(self.blockchain.head) < len(r.json()):
                        self.blockchain.from_dict_list(r.json())
                        try:
                            self.blockchain.validate()
                            origin_address = address
                        except Exception as e:
                            logger.error(f"Error fetching longest chain: {e}")
                            self.blockchain = None
            except requests.exceptions.ConnectionError:
                disconnected_address_set.add(address)

        self.known_node_address_set.difference_update(disconnected_address_set)
        if self.blockchain is not None:
            self.account_dict = self.blockchain.initialize_accounts()

        if origin_address is None:
            logger.info(f"Did not receive blockchain")
        else:
            logger.info(f"Received longest blockchain from address {origin_address}")

    def join_network(self):
        # 1. Ask seed nodes for their known nodes
        self._request_addresses_from_known_nodes()

        # 2. Advertise itself to known nodes
        self._advertise_to_known_nodes()

        # 3. get blockchain from known nodes
        self._get_longest_blockchain()

    ##### ICO related functions #####

    def initialize_ico_block(self, block: Block):
        block_hash_hex = binascii.hexlify(block.block_hash)
        logger.info(f"Initializing ICO block {block_hash_hex}")

        block.validate(self.account_dict)

        if self.blockchain is not None:
            self.blockchain.add_new_block(block)
            block.update_account_dict(self.account_dict)
        else:
            self.blockchain = Blockchain(block)
            self.account_dict = self.blockchain.initialize_accounts()

    ##### P2P data handling #####

    def accept_new_node(self, address: str):
        logger.info(f"Accepted node {address}")
        self.known_node_address_set.add(address)

    async def accept_new_transaction(self, transaction: Transaction, origin: str):
        transaction_hash_hex = binascii.hexlify(
            transaction.transaction_hash)
        logger.info(
            f"Received transaction {transaction_hash_hex} from {origin}")

        # 1. Check if transaction in transaction pool
        async with self.lock:
            if transaction.transaction_hash in self.transaction_pool:
                return None

        # 2. Validate transaction
        transaction.validate(self.account_dict[transaction.transaction_source.source_public_key_hex])

        # 3. Add to transaction pool
        async with self.lock:
            self.transaction_pool[transaction_hash_hex] = transaction

        # 4. Broadcast to other nodes
        await self._broadcast_transaction(transaction, origin)

        # 5. TODO: Add block to blockchain if the condition is met

    async def accept_new_block(self, block: Block, origin: str):
        block_hash_hex = binascii.hexlify(block.block_hash)
        logger.info(f"Received block {block_hash_hex} from {origin}")

        # 1. Validate block
        block.validate(self.account_dict)

        # 2. TODO: take action is the block is invalid (slashing)

        # 3. Add block to blockchain
        async with self.lock:
            if self.blockchain is not None:
                self.blockchain.add_new_block(block)
            else:
                self.blockchain = Blockchain(block)

        # 4. Apply account stake and balance changes. Give tokens to the validator
        block.update_account_dict(self.account_dict)

        # 5. Remove transactions from transaction pool
        async with self.lock:
            for transaction in block.transaction_list:
                transaction_hash_hex = binascii.hexlify(
                    transaction.transaction_hash)
                self.transaction_pool.pop(transaction_hash_hex, None)
                self.transaction_broadcasted.pop(transaction_hash_hex, None)

        # 6. Broadcast
        await self._broadcast_block(block, origin)

    async def _broadcast_transaction(self, transaction: Transaction, origin: str):
        transaction_hash_hex = binascii.hexlify(transaction.transaction_hash)

        # add transaction to broadcasted set
        async with self.lock:
            if transaction_hash_hex not in self.transaction_broadcasted:
                self.transaction_broadcasted[transaction_hash_hex] = set([])

        # send transcation data to other nodes
        disconnected_address_set = set([])
        for address in self.known_node_address_set:
            if address == origin or address in self.transaction_broadcasted[transaction_hash_hex]:
                continue
            url = address + constants.TRANSACTION_VALIDATION_PATH
            headers = {"Content-type": "application/json"}
            data = transaction.to_dict()
            data["origin"] = self.address
            try:
                async with self.lock:
                    self.transaction_broadcasted[transaction_hash_hex].add(
                        address)
                # requests.post(url=url, headers=headers, json=data)
                async with httpx.AsyncClient() as client:
                    await client.post(url, headers=headers, json=data)
                logger.info(
                    f'Broadcasted transaction {transaction_hash_hex} to {address}')
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
                logger.info(f"Detected disconnection of {address}")
                disconnected_address_set.add(address)

        async with self.lock:
            self.known_node_address_set.difference_update(
                disconnected_address_set)

    async def _broadcast_block(self, block: Block, origin: str):
        block_hash_hex = binascii.hexlify(block.block_hash)

        # add block to block_hash_hex to address set dict
        async with self.lock:
            if block_hash_hex not in self.block_broadcasted:
                self.block_broadcasted[block_hash_hex] = set([])

        # send block data to other nodes
        disconnected_address_set = set([])
        for address in self.known_node_address_set:
            if address == origin or address in self.block_broadcasted[block_hash_hex]:
                continue
            url = address + constants.BLOCK_VALIDATION_PATH
            headers = {"Content-type": "application/json"}
            data = block.to_dict()
            data["origin"] = self.address
            try:
                async with self.lock:
                    self.block_broadcasted[block_hash_hex].add(address)
                async with httpx.AsyncClient() as client:
                    await client.post(url, headers=headers, json=data)
                logger.info(f'Broadcasted block {block_hash_hex} to {address}')
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
                logger.info(f"Detected disconnection of {address}")
                disconnected_address_set.add(address)

        async with self.lock:
            self.known_node_address_set.difference_update(
                disconnected_address_set)

    ##### PoS Consesus functions #####
    def _generate_validator_rand(self):
        return int(secrets.token_hex(8))

    def accept_validator_rand(self, public_key_hex: bytes, rand: int):
        # TODO: determine disconnected validator
        pass

    def broadcast_validator_rand(self):
        pass

    def create_block(self):
        # 1. order transactions in transaction pool by the amount of stake
        pass
