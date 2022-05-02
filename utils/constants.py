import os

EXAMPLE_DATA_DIR = os.path.join(os.getcwd(), "example_data")
SEED_NODES_FILE = os.path.join(EXAMPLE_DATA_DIR, "seed_nodes.json")
ICO_PUBLIC_KEY_FILE = os.path.join(os.getcwd(), "genesis", "ico_accounts.json")

KNOWN_NODES_PATH = "/known_nodes"
NODE_REQUEST_PATH = "/node"
BLOCKCHAIN_REQUEST_PATH = "/blockchain"
TRANSACTION_VALIDATION_PATH = "/validation/transaction"
BLOCK_VALIDATION_PATH = "/validation/block"

ACCOUNTS_PATH = "/accounts"

ICO_TOKENS = 1_000_000
VALIDATION_REWARD = 100
