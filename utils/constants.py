import os

EXAMPLE_DATA_DIR = os.path.join(os.getcwd(), "example_data")
SEED_NODES_FILE = os.path.join(EXAMPLE_DATA_DIR, "seed_nodes.json")
ICO_PUBLIC_KEY_FILE = os.path.join(os.getcwd(), "genesis", "ico_accounts.json")

KNOWN_NODES_PATH = "/known_nodes"
NODE_REQUEST_PATH = "/node"
TRANSACTION_VALIDATION_PATH = "/validation/transaction"
BLOCK_VALIDATION_PATH = "/validation/block"
VALIDATOR_RAND_PATH = "/validator/rand"

ICO_TOKENS = 1_000_000
VALIDATION_REWARD = 100  # TODO: make it a function of staked tokens in a block
VALIATOR_MINIMUM_STAKE = 10  # minimum staked token to become a validator # TODO: apply logi based on this number
MAX_TX_PER_BLOCK = 20  # maximum number of transactions per block # TODO: can calculate precisely backwards form desired block size

MIN_VALIDATOR_CNT = 3  # minimum number of validators needed to create a block

# Make the RANDAO function also consider the most recent timestamp of becoming forger

STORAGE_PATH = os.path.join(os.getcwd(), "storage")
