import binascii
from http.client import HTTPException
import logging
from typing import List

from fastapi import APIRouter, Depends

from block.block import create_block_from_dict
from block.validator_rand import ValidatorRand
from node.models import BlockValidationRequest, NodeAddress, TransactionValidationRequest, ValidatorRandRequest
from node.node import Node
from runner.deps import get_node
from transaction.transaction_utils import create_transaction_from_dict
from utils import constants

logger = logging.getLogger(__name__)

router = APIRouter()


##### Endpoints that other nodes call #####

@router.post(constants.BLOCK_VALIDATION_PATH, response_model=None)
async def validate_block(
    blockRequest: BlockValidationRequest,
    node: Node = Depends(get_node)
):
    # other nodes hit this endpoint to broadcast block to this node

    # 1. create block instance
    previous_block = None
    if blockRequest.previous_block_hash_hex is not None:
        # TODO: what if the block does not reach this node in order?
        # make a block pool to store candidate blocks
        # for now, just check if the previous block is head
        if node.blockchain.head.block_hash != binascii.unhexlify(blockRequest.previous_block_hash_hex.encode('utf-8')):
            logger.error("Requested block is not linked to the current head")
            raise HTTPException(
                status_code=409,
                detail="Requested block is not linked to the current head"
            )
        previous_block = node.blockchain.head

    block_dict = blockRequest.dict()
    origin = block_dict["origin"]
    del block_dict["origin"]
    block = create_block_from_dict(blockRequest.dict(), previous_block)

    # 2. add block to blockchain
    logger.info("Adding new block to blockchain")
    await node.accept_block(block, origin)


@router.post(constants.TRANSACTION_VALIDATION_PATH, response_model=None)
async def validate_transaction(
    transactionRequest: TransactionValidationRequest,
    node: Node = Depends(get_node)
):
    # other nodes hit this endpoint to broadcast transaction to this node

    # 1. create Transaction instance
    transaction_dict = transactionRequest.dict()
    origin = transaction_dict["origin"]
    del transaction_dict["origin"]
    transaction = create_transaction_from_dict(transactionRequest.dict())

    # 2. add transaction to transaction pool
    await node.accept_transaction(transaction, origin)


@router.post(constants.NODE_REQUEST_PATH, response_model=None)
async def accept_new_node(
    data: NodeAddress,
    node: Node = Depends(get_node)
):
    # add the new node to known node address list
    node.accept_new_node(data.address)


@router.get(constants.KNOWN_NODES_PATH, response_model=List[str])
async def get_known_nodes(node: Node = Depends(get_node)):
    # return known nodes
    return list(node.known_node_address_set)


@router.post(constants.VALIDATOR_RAND_PATH, response_model=None)
async def accept_validator_rand(
    data: ValidatorRandRequest,
    node: Node = Depends(get_node)
):
    # accept the random number passed by a validator

    # TODO: return ack to allow the broadcaster to retry if there is any error
    validator_rand = ValidatorRand(
        data.validator_public_key_hex.encode('utf-8'),
        data.previous_block_hash_hex.encode('utf-8'),
        timestamp=data.timestamp,
        rand=data.rand,
        signature=binascii.unhexlify(data.signature_hex.encode('utf-8'))
    )
    await node.accept_validator_rand(validator_rand)