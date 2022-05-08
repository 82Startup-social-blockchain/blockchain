import binascii
import json
import os

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization

from block.blockchain import Blockchain
from genesis.initial_block import create_initial_block, load_initial_accounts
from node.node import Node
from utils import constants
from utils.crypto import get_public_key_hex


with open(os.path.join(os.getcwd(), "genesis", os.environ["ACCOUNT_KEY_FILE_NAME"]), 'r') as fp:
    private_key_serialized = binascii.unhexlify(json.load(fp).encode('utf-8'))
PRIVATE_KEY = serialization.load_der_private_key(private_key_serialized, None)
PUBLIC_KEY = PRIVATE_KEY.public_key()
PUBLIC_KEY_HEX = get_public_key_hex(PUBLIC_KEY)

node = Node(os.environ["ADDRESS"], private_key=PRIVATE_KEY)
print(f"[INFO] Initialized node with public key: {PUBLIC_KEY_HEX}")

node.join_network()

# initialize blockchain with given data - assume INIT_BLOCKCHAIN_FILE_NAME contains ICO data
if "INIT_BLOCKCHAIN_FILE_NAME" in os.environ:
    with open(os.path.join(constants.EXAMPLE_DATA_DIR, os.environ["INIT_BLOCKCHAIN_FILE_NAME"]), 'r') as fp:
        blockchain_dict_list = json.load(fp)
    blockchain = Blockchain()
    blockchain.from_dict_list(blockchain_dict_list)
    node.blockchain = blockchain
    node.account_dict = blockchain.initialize_accounts()

# if node does not have blockchain initialize genesis block that has ICO details
if node.blockchain is None or node.blockchain.head is None:
    ico_accounts = load_initial_accounts(constants.ICO_PUBLIC_KEY_FILE)
    block = create_initial_block(ico_accounts)
    node.initialize_ico_block(block)


def get_node() -> Node:
    return node


def get_private_key() -> ec.EllipticCurvePrivateKey:
    return PRIVATE_KEY


def get_public_key() -> ec.EllipticCurvePublicKey:
    return PUBLIC_KEY


def get_public_key_hex() -> bytes:
    return PUBLIC_KEY_HEX
