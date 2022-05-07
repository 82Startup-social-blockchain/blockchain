from __future__ import annotations
import binascii
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from block.block import Block


class BlockValidationError(Exception):
    def __init__(self, block: Optional[Block], message="", block_hash: Optional[bytes] = None):
        if block is not None:
            base_message = f"(block: {binascii.hexlify(block.block_hash)})"
        elif block_hash is not None:
            base_message = f"(block: {binascii.hexlify(block_hash)}"

        if message != "":
            error_message = f"{message} {base_message}"
        else:
            error_message = base_message
        super().__init__(error_message)


class BlockValidatorError(BlockValidationError):
    def __init__(self, block: Block, message=""):
        super().__init__(block, message=f"[BlockValidatorError] {message}")


class BlockNotHeadError(BlockValidationError):
    def __init__(self, block: Block, message="", block_hash=None):
        super().__init__(block, message=f"[BlockNotHeadError] {message}", block_hash=block_hash)


class BlockPreviousBlockError(BlockValidationError):
    def __init__(self, block: Block, message=""):
        super().__init__(block, message=f"[BlockPreviousBlockError] {message}")
