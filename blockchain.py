import binascii
import random
from collections import defaultdict
import pickle
import logging

from ipv8.community import Community, CommunitySettings
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer

from block import Block

# Amount of peers to send message to
k = 2

logging.basicConfig(filename='blockchain.log', level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')


@dataclass(msg_id=1)  # The value 1 identifies this message and must be unique per community
class Transaction:
    sender: bytes
    receiver: bytes
    amount: int
    nonce: int = 1
    ttl: int = 3


@dataclass(msg_id=2)
class BlockMessage:
    hash: str
    block: bytes


class MyCommunity(Community):
    community_id = b'harbourspaceuniverse'

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.counter = 1
        self.max_messages = 5
        self.executed_checks = 0

        self.pending_txs = []
        self.finalized_txs = []
        self.balances = defaultdict(lambda: 1000)
        self.blocks = []  # List to store finalized blocks
        self.current_block = Block('0')  # Current working block

        self.add_message_handler(Transaction, self.on_transaction)
        self.add_message_handler(BlockMessage, self.on_block)

    def started(self, id) -> None:
        logging.info('Community started')
        # Testing purpose
        if id == 1:
            self.register_task("tx_create", self.create_transaction, delay=1, interval=5)
        # WIP: Check if this is the right way to check transactions
        self.register_task("check_txs", self.check_transactions, delay=1, interval=5)

    def peers_found(self):
        return len(self.get_peers()) > 0

    def get_peer_id(self, peer: Peer = None):
        return binascii.hexlify(peer.mid).decode()

    def create_transaction(self):
        if not self.peers_found():
            print(f'[Node {self.get_peer_id(self.my_peer)}] No peers found')
            logging.info(f'[Node {self.get_peer_id(self.my_peer)}] No peers found')
            return

        print(f'[Node {self.get_peer_id(self.my_peer)}] Creating transaction')
        logging.info(f'[Node {self.get_peer_id(self.my_peer)}] Creating transaction')
        peer = random.choice([i for i in self.get_peers()])
        peer_id = peer.mid

        tx = Transaction(self.my_peer.mid,
                         peer_id,
                         10,
                         self.counter)
        self.counter += 1
        print(f'[Node {self.get_peer_id(self.my_peer)}] Sending transaction {tx.nonce} to {self.get_peer_id(peer)}')
        logging.info(
            f'[Node {self.get_peer_id(self.my_peer)}] Sending transaction {tx.nonce} to {self.get_peer_id(peer)}')

        self.ez_send(peer, tx)

        # WIP: We need this?
        # if self.counter > self.max_messages:
        #     self.cancel_pending_task("tx_create")
        #     self.stop()
        #     return

    def check_transactions(self):
        print(f'[Node {self.get_peer_id(self.my_peer)}] Checking transactions')
        logging.info(f'[Node {self.get_peer_id(self.my_peer)}] Checking transactions')

        for tx in self.pending_txs:
            if self.balances[tx.sender] - tx.amount >= 0:
                self.balances[tx.sender] -= tx.amount
                self.balances[tx.receiver] += tx.amount
                self.pending_txs.remove(tx)
                self.finalized_txs.append(tx)
                self.current_block.add_transaction(tx)

                if self.current_block.is_full():
                    print('Block is full')
                    self.finalize_and_broadcast_block()
                    break

    @lazy_wrapper(Transaction)
    async def on_transaction(self, peer: Peer, payload: Transaction) -> None:
        my_id = self.get_peer_id(self.my_peer)

        print(f'[Node {my_id}] Received transaction', payload.nonce, 'from', self.get_peer_id(peer))
        logging.info(f'[Node {my_id}] Received transaction {payload.nonce} from {self.get_peer_id(peer)}')

        # Add to pending transactions
        if (payload.sender, payload.nonce) not in [(tx.sender, tx.nonce) for tx in self.finalized_txs] and (
                payload.sender, payload.nonce) not in [(tx.sender, tx.nonce) for tx in self.pending_txs]:
            self.pending_txs.append(payload)

        # If we are connected to more than k peers, we can gossip
        # only if the ttl is greater than 0
        if len(self.get_peers()) > k and payload.ttl > 0:
            payload.ttl -= 1

            # push gossip to k random peers
            get_peers_to_distribute = random.sample(self.get_peers(), k)
            for peer in get_peers_to_distribute:
                self.ez_send(peer, payload)

    @lazy_wrapper(BlockMessage)
    async def on_block(self, peer: Peer, payload: BlockMessage) -> None:
        unserialized_block = pickle.loads(payload.block)
        print(unserialized_block)

        # Check if the block is already in the chain
        if payload.hash not in [block.merkle_tree.get_root_hash() for block in self.blocks]:
            print(f'Block {payload.hash} not in my chain {self.get_peer_id(peer)}')
            logging.info(f'Block {payload.hash} not in my chain {self.get_peer_id(peer)}')
            self.blocks.append(unserialized_block)

        # WIP: Necessary check?
        # Check if the previous block hash is indeed the past block

    def finalize_and_broadcast_block(self):
        self.current_block.merkle_tree.recalculate_tree()
        new_block_hash = self.current_block.merkle_tree.get_root_hash()
        print(f'New block hash: {new_block_hash}')
        logging.info(f'New block hash: {new_block_hash}')
        self.blocks.append(self.current_block)
        serialized_block = pickle.dumps(self.current_block)
        self.current_block = Block(new_block_hash)

        self.broadcast_new_block(new_block_hash, serialized_block)

    def broadcast_new_block(self, block_hash, serialized_block):
        blockMessage = BlockMessage(block_hash, serialized_block)

        for peer in self.get_peers():
            self.ez_send(peer, blockMessage)