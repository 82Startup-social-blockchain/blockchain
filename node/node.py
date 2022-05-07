import asyncio
import binascii
import itertools
import json
import time
from typing import Dict, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
import httpx
import requests

from block.block import Block
from block.block_exception import BlockPreviousBlockError, BlockValidationError, BlockValidatorError
from block.blockchain import Blockchain
from block.validator_rand import ValidatorRand
from transaction.transaction import Transaction
from utils import constants
from node.utils import get_stakes_from_accounts
from utils.crypto import get_public_key_hex


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

        self.transaction_pool: Dict[bytes, Transaction] = dict()  # { transaction_hash_hex: Transaction }
        self.transaction_broadcasted = dict()  # { transactino_hash_hex: set }
        self.block_broadcasted = dict()  # { block_hash_hex: set }

        self.account_dict = dict()  # { account_public_key_hex: Account }
        self.validator_rand_dict: Dict[bytes, int] = dict()  # { validator_public_key_hex: random number }
        self.block_validator_dict: Dict[bytes, bytes] = dict()  # { previous_block_hash_hex: validator }

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
                print(f"[INFO] Advertised to node {address}")
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
                        print(f"[ERROR] Error fetching longest chain: {e}")
                        self.blockchain = None
                else:
                    # TODO: update after head instead of re-initializing
                    if len(self.blockchain.head) < len(r.json()):
                        self.blockchain.from_dict_list(r.json())
                        try:
                            self.blockchain.validate()
                            origin_address = address
                        except Exception as e:
                            print(f"[ERROR] Error fetching longest chain: {e}")
                            self.blockchain = None
            except requests.exceptions.ConnectionError:
                disconnected_address_set.add(address)

        self.known_node_address_set.difference_update(disconnected_address_set)
        if self.blockchain is not None:
            self.account_dict = self.blockchain.initialize_accounts()

        if origin_address is None:
            print(f"[WARN] Did not receive blockchain")
        else:
            print(f"[INFO] Received longest blockchain from address {origin_address}")

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
        print(f"[INFO] Initializing ICO block {block_hash_hex}")

        block.validate(self.account_dict)

        if self.blockchain is not None:
            self.blockchain.add_new_block(block)
            block.update_account_dict(self.account_dict)
        else:
            self.blockchain = Blockchain(block)
            self.account_dict = self.blockchain.initialize_accounts()
        print(f"[INFO] Account stakes after ico block initialization: {get_stakes_from_accounts(self.account_dict)}")

    ##### P2P data handling #####

    def accept_new_node(self, address: str):
        print(f"[INFO] Accepted node {address}")
        self.known_node_address_set.add(address)

    async def accept_transaction(self, transaction: Transaction, origin: str):
        transaction_hash_hex = binascii.hexlify(
            transaction.transaction_hash)
        print(f"[INFO] Received transaction {transaction_hash_hex} from {origin}")

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
                print(f'[INFO] Broadcasted transaction {transaction_hash_hex} to {address}')
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
                print(f"[WARN] Detected disconnection of {address}")
                disconnected_address_set.add(address)

        async with self.lock:
            self.known_node_address_set.difference_update(
                disconnected_address_set)

    async def accept_block(self, block: Block, origin: str):
        block_hash_hex = binascii.hexlify(block.block_hash)
        print(f"[INFO] Received block {block_hash_hex} from {origin}")

        # 1. Validate block
        block.validate(self.account_dict)

        # 2. Check if the validator is the right validator
        # The genesis block will not be accepted through this method => previous_block or previous_block_hash_hex not None
        if block.previous_block is not None:
            previous_block_hash_hex = binascii.hexlify(block.previous_block.block_hash)
        elif block.previous_block is not None:
            previous_block_hash_hex = block.previous_block_hash_hex
        else:
            raise BlockPreviousBlockError(block, message="Previous block hash hex nonexistent")
        if previous_block_hash_hex not in self.block_validator_dict:
            raise BlockValidatorError(block, message="No validator of the received block")
        if self.block_validator_dict[previous_block_hash_hex] != block.validator_public_key_hex:
            raise BlockValidationError(block, message="Wrong validator of the received block")

        # 3. Add block to blockchain if it is the most recent
        async with self.lock:
            if self.blockchain is not None:
                if block.previous_block.block_hash == self.blockchain.head.block_hash:
                    self.blockchain.add_new_block(block)
            else:
                self.blockchain = Blockchain(block)

        # 4. Apply account stake and balance changes. Give tokens to the validator.
        block.update_account_dict(self.account_dict)

        # 5. Remove transactions from transaction pool
        async with self.lock:
            for transaction in block.transaction_list:
                transaction_hash_hex = binascii.hexlify(
                    transaction.transaction_hash)
                self.transaction_pool.pop(transaction_hash_hex, None)
                self.transaction_broadcasted.pop(transaction_hash_hex, None)

        # 6. TODO: clear validator_rand_dict

        # 7. Broadcast
        await self.broadcast_block(block, origin)

    async def broadcast_block(self, block: Block, origin: str):
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
                print(f'[INFO] Broadcasted block {block_hash_hex} to {address}')
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
                print(f"[WARN] Detected disconnection of {address}")
                disconnected_address_set.add(address)

        async with self.lock:
            self.known_node_address_set.difference_update(
                disconnected_address_set)

    async def accept_validator_rand(self, validator_rand: ValidatorRand):
        print(f"[INFO] Received validator rand {validator_rand.rand} from validator {validator_rand.validator_public_key_hex}")
        # 1. Validate validator_rand
        if validator_rand.signature is None:
            print(f"[ERROR] Signature None from validator {validator_rand.validator_public_key_hex}")
            raise InvalidSignature

        public_key_serialized = binascii.unhexlify(validator_rand.validator_public_key_hex)
        public_key = serialization.load_der_public_key(public_key_serialized)
        public_key.verify(
            validator_rand.signature,
            json.dumps(validator_rand._to_presigned_dict()).encode('utf-8'),
            ec.ECDSA(hashes.SHA256())
        )
        # TODO: check that rand is non-negative

        # 2. Add to validator rand dict
        # TODO: What if validator sends rand key multiple times? - choose the earliest one?
        if validator_rand.validator_public_key_hex not in self.validator_rand_dict:
            self.validator_rand_dict[validator_rand.validator_public_key_hex] = validator_rand.rand

    async def broadcast_validator_rand(self, validator_rand: ValidatorRand):
        # TODO: assume receiving same number multiple times like block and transaction

        # 1. Broadcast the validator rand to known nodes
        disconnected_address_set = set([])
        for address in self.known_node_address_set:
            url = address + constants.VALIDATOR_RAND_PATH
            headers = {"Content-type": "application/json"}
            data = validator_rand.to_dict()
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(url, headers=headers, json=data)
                print(f'[INFO] Broadcasted validator rand {data["rand"]} to {address}')
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout):
                print(f"[WARN] Detected disconnection of {address}")
                disconnected_address_set.add(address)

        async with self.lock:
            self.known_node_address_set.difference_update(
                disconnected_address_set)
            self.validator_rand_dict[validator_rand.validator_public_key_hex] = validator_rand.rand

    ##### PoS Consesus functions #####

    def create_validator_rand(self, public_key_hex: bytes) -> Optional[ValidatorRand]:
        if self.blockchain is None:
            return None

        validator_rand = ValidatorRand(public_key_hex, binascii.hexlify(self.blockchain.head.block_hash))
        validator_rand.sign(self.private_key)
        return validator_rand

    def _get_validator(self) -> bytes:
        # assume that all stake amounts and random numbers are integers
        account_stake_dict = get_stakes_from_accounts(self.account_dict)
        stake_sum = sum(account_stake_dict.values())
        rand_num = sum(self.validator_rand_dict.values()) % stake_sum

        validator_arr, stake_arr = list(zip(*sorted(account_stake_dict.items(), key=lambda x: x[1])))
        for i, stake in enumerate(itertools.accumulate(stake_arr)):
            if rand_num < stake:
                validator = validator_arr[i]
                break
        return validator

    def create_block(self) -> Block:
        # 1. order transactions in transaction pool by the amount of stake
        # TODO: eventual inclusion?
        account_stake_dict = get_stakes_from_accounts(self.account_dict)
        transaction_candidates = []  # tuple of transaction and account stake
        for transaction_hash_hex in self.transaction_pool:
            transaction = self.transaction_pool[transaction_hash_hex]
            transaction_candidates.append((transaction, account_stake_dict[transaction.transaction_source.source_public_key_hex]))
        transaction_candidates = sorted(transaction_candidates, key=lambda x: x[1], reverse=True)[:constants.MAX_TX_PER_BLOCK]
        tx_list = list(map(lambda x: x[0], transaction_candidates))
        block = Block(
            None,
            binascii.hexlify(self.blockchain.head.block_hash),
            tx_list,
            get_public_key_hex(self.private_key.public_key()),
            time.time()
        )
        print(f"[INFO] Created block {block.to_dict()}")
        return block

    def run_consensus_protocol(self) -> bool:
        account_stake_dict = get_stakes_from_accounts(self.account_dict)

        # 1. check if the node has received rand from all validators
        if set(account_stake_dict.keys()) != set(self.validator_rand_dict.keys()):
            # TODO: what if nodes to slash differ for different nodes?
            # TODO: add slashing to transaction pool?
            print(account_stake_dict)
            print(self.validator_rand_dict)
            n_missing = len(account_stake_dict) - len(self.validator_rand_dict)
            print(f"[WARN] Missing {n_missing} validators's rand - {set(account_stake_dict.keys()).difference(set(self.validator_rand_dict.keys()))}")
            pass

        # 2. get validator
        validator = self._get_validator()
        print(f"[INFO] Validator chosen - {validator}")

        # 3. save validator to validate signed block later
        self.block_validator_dict[binascii.hexlify(self.blockchain.head.block_hash)] = validator

        return validator == get_public_key_hex(self.private_key.public_key())
