from __future__ import annotations
import binascii
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from block.block import Block


class BlockValidationError(Exception):
    def __init__(self, block: Block, message=""):
        base_message = f"(block: {binascii.hexlify(block.block_hash)})"
        if message != "":
            error_message = f"{message} {base_message}"
        else:
            error_message = base_message
        super().__init__(error_message)


class BlockValidatorError(BlockValidationError):
    def __init__(self, block: Block, message=""):
        super().__init__(block, message=f"[BlockValidatorError] {message}")
