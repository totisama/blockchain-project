import binascii
import logging
import random
from asyncio import run
from collections import defaultdict
from hashlib import sha256

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8

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
    signature: bytes
    public_key: bytes


@dataclass(msg_id=2)
class BlockMessage:
    hash: str
    block: Block
    ttl: int = 3

class MyCommunity(Community):
    community_id = b'harbourspaceuniverse'

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.counter = 1
        self.max_messages = 5
        self.executed_checks = 0

        self.pending_txs = {}
        self.finalized_txs = {}
        self.balances = defaultdict(lambda: 1000)
        self.blocks = []  # List to store finalized blocks
        self.current_block = Block('0')  # Current working block

        self.add_message_handler(Transaction, self.on_transaction)
        self.add_message_handler(BlockMessage, self.receive_block)

    def started(self, id) -> None:
        logging.info('Community started')

        # Testing purpose
        if id == 1:
            random_transaction_interval = random.randint(5, 10)
            self.register_task("tx_create", self.create_transaction, delay=1, interval=random_transaction_interval)

        random_check_interval = random.randint(5, 10)
        self.register_task("check_txs", self.block_creation, delay=1, interval=random_check_interval)

    def peers_found(self):
        return len(self.get_peers()) > 0

    def get_peer_id(self, peer: Peer = None):
        return binascii.hexlify(peer.mid).decode()

    def get_tx_hash(self, tx: Transaction) -> bytes:
        tx_copy = Transaction(tx.sender, tx.receiver, tx.amount, tx.nonce, tx.ttl)
        return sha256(self.serializer.pack_serializable(tx_copy)).digest()

    def get_tx_bytes(self, tx: Transaction) -> bytes:
        tx_copy = Transaction(tx.sender, tx.receiver, tx.amount, tx.nonce, tx.ttl)
        return self.serializer.pack_serializable(tx_copy)

    def create_transaction(self):
        if not self.peers_found():
            logging.info(f'[Node {self.get_peer_id(self.my_peer)}] No peers found')
            return

        logging.info(f'[Node {self.get_peer_id(self.my_peer)}] Creating transaction')
        peer = random.choice([i for i in self.get_peers()])
        peer_id = peer.mid

        tx = Transaction(self.my_peer.mid,
                         peer_id,
                         10,
                         self.counter)
        self.counter += 1
        logging.info(f'[Node {self.get_peer_id(self.my_peer)}] Sending transaction {tx.nonce} to {self.get_peer_id(peer)}')
        self.ez_send(peer, tx)

        receiver_peer = random.choice([i for i in self.get_peers()])
        peer_id = receiver_peer.mid

        # ttl = 3 when creating a tx
        tx = Transaction(self.my_peer.mid, peer_id, 10, self.counter)
        tx.public_key = self.my_peer.mid
        tx.signature = self.crypto.create_signature(self.my_peer.key, self.serializer.pack_serializable(tx))
        print(f'[Node {self.get_peer_id(self.my_peer)}] Sending transaction {tx.nonce} to {self.get_peer_id(receiver_peer)}')
        self.pending_txs[self.get_tx_hash(tx)] = tx
        self.ez_send(receiver_peer, tx)
        self.counter += 1

        # WIP: We need this?
        # if self.counter > self.max_messages:
        #     self.cancel_pending_task("tx_create")
        #     self.stop()
        #     return

    def block_creation(self):
        # WIP: get every known peer, not only the ones im connected to
        peers = self.get_peers()
        peers.append(self.my_peer)
        selectedPeer = random.choice(peers)

        if not selectedPeer.mid == self.my_peer.mid:
            return

        for tx in self.pending_txs:
            self.pending_txs.remove(tx)
            self.finalized_txs.append(tx)
            self.current_block.add_transaction(tx)

            if self.current_block.is_full():
                print(f'[Node {self.get_peer_id(self.my_peer)}] Chosen one')
                self.finalize_and_broadcast_block()
                break

    # process txs from pending_txs
    def check_transactions(self):
        print(f'[Node {self.get_peer_id(self.my_peer)}] Checking transactions')

        for tx in self.pending_txs:
            if self.balances[tx.sender] - tx.amount >= 0:
                self.balances[tx.sender] -= tx.amount
                self.balances[tx.receiver] += tx.amount
                self.pending_txs.pop(self.get_tx_hash(tx))
                self.finalized_txs[self.get_tx_hash(tx)] = tx
                self.current_block.add_transaction(tx)
            else:
                self.pending_txs.pop(self.get_tx_hash(tx))

            if self.current_block.is_full():
                print('Block is full')
                self.finalize_and_broadcast_block()
                break

    @lazy_wrapper(Transaction)
    async def on_transaction(self, peer: Peer, tx: Transaction) -> None:
        my_id = self.get_peer_id(self.my_peer)

        logging.info(f'[Node {my_id}] Received transaction {tx.nonce} from {self.get_peer_id(peer)}')

        tx_hash = self.get_tx_hash(tx)
        if tx_hash in self.finalized_txs or tx_hash in self.pending_txs:
            return

        signature = tx.signature
        public_key = tx.public_key
        if not self.crypto.is_valid_signature(tx.public_key, self.get_tx_bytes(tx), signature):
            return

        tx.public_key = public_key
        tx.signature = signature
        self.pending_txs[self.get_tx_hash(tx)] = tx

        # todo
        # If we are connected to more than k peers, we can gossip
        # only if the ttl is greater than 0
        if len(self.get_peers()) > k and tx.ttl > 0:
            tx.ttl -= 1

            # push gossip to k random peers
            get_peers_to_distribute = random.sample(self.get_peers(), min(k, len(self.get_peers())))
            for peer in get_peers_to_distribute:
                self.ez_send(peer, tx)

    @lazy_wrapper(BlockMessage)
    async def receive_block(self, peer: Peer, payload: BlockMessage) -> None:
        print('----------on block----------')
        print(payload)

        print(payload.block.previous_hash)
        print(payload.block.merkle_hash)
        print(payload.block.transactions)

        # Check if the block is already in the chain
        # if payload.hash not in [block.get_merkle_hash() for block in self.blocks]:
        #     print(f'Block {payload.hash} not in my chain {self.get_peer_id(peer)}')
        #     logging.info(f'Block {payload.hash} not in my chain {self.get_peer_id(peer)}')
        #     self.blocks.append(payload.block)

        # Remove block transactions from my pending_txs list
        # for tx in unserialized_block.transactions:
        #     if (tx.sender, tx.nonce) in [(tx.sender, tx.nonce) for tx in self.pending_txs]:
        #         self.pending_txs.remove(tx)

    def finalize_and_broadcast_block(self):
        self.current_block.update_tree()
        new_block_hash = self.current_block.get_merkle_hash()
        print(f'New block hash: {new_block_hash}')
        logging.info(f'New block hash: {new_block_hash}')
        self.blocks.append(self.current_block)

        self.broadcast_block(new_block_hash, self.current_block)
        self.current_block = Block(new_block_hash)

    def broadcast_block(self, block_hash: str, block: Block):
        blockMessage = BlockMessage(block_hash, block)

        for peer in self.get_peers():
            self.ez_send(peer, blockMessage)


async def start_communities() -> None:
    # We create 7 peers
    for i in range(1, 4):
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key("my peer", "medium", f"ec{i}.pem")
        builder.add_overlay("MyCommunity", "my peer",
                            [WalkerDefinition(Strategy.RandomWalk,
                                              10, {'timeout': 3.0})],
                            default_bootstrap_defs, {}, [('started', i)])
        await IPv8(builder.finalize(),
                   extra_communities={'MyCommunity': MyCommunity}).start()
    await run_forever()
run(start_communities())
