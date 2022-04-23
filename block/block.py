class BlockHeader:
    def __init__(
        self,
        previous_block_hash,
        tx_merkle_root, # merkle root of transactions => used for validating transactions
        block_timestamp, # timestamp of when the block is added to blockchain
        block_idx, # the index of block in the blockchain
    ):
        self.previous_block_hash = previous_block_hash
        self.tx_merkle_root = tx_merkle_root
        self.block_timestamp = block_timestamp
        self.block_idx = block_idx

    def __str__(self):
        pass

class Block:
    def __init__(
        self,
        block_header: BlockHeader,
        previous_block=None
    ):
        self.block_header = block_header
        self.previous_block = previous_block

    def __str__(self):
        pass




# References

# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/blockchain.go#L126
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/network.go#L2099
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/network.go#L1679
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/network.go#L2327
# https://github.com/deso-protocol/core/blob/85437b36ff233204195f99a9833ded435aa32248/lib/blockchain.go#L403

