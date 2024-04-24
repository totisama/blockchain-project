from ipv8.messaging.payload_dataclass import dataclass

from block import Block


@dataclass(msg_id=4)
class BlockRequest:
    block_hash: str


@dataclass(msg_id=5)
class BlockResponse:
    block: Block
