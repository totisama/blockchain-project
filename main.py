import binascii
import logging
import random
import sys
from asyncio import run
from collections import defaultdict
from typing import Dict,Tuple

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8

from block import Block
from transaction import Transaction

import time

# Amount of peers to send message to
k = 2

logfile = 'logfile.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',handlers=[
        logging.StreamHandler(),  # Log to stdout
        logging.FileHandler(logfile)  # Log to a file
    ])


@dataclass(msg_id=2)
class BlockMessage:
    hash: str
    block: Block
    ttl: int = 3

@dataclass(msg_id=3)
class PeersMessage:
    mid: bytes
    ttl: int = 3


class MyCommunity(Community):
    community_id = b'harbourspaceuniverse'

    def __init__(self, settings: CommunitySettings) -> None:
        super().__init__(settings)
        self.counter = 1
        self.max_messages = 5
        self.executed_checks = 0

        self.pending_txs: Dict[bytes, Transaction] = {}
        # self.pending_txs: Dict[bytes, Tuple[Transaction, float]] = {}

        self.finalized_txs: Dict[bytes, Transaction] = {}
        self.balances = defaultdict(lambda: 1000)
        self.blocks = []  # List to store finalized blocks
        self.current_block = Block('0')  # Current working block

        self.known_peers_mid = set()

        self.add_message_handler(Transaction, self.on_transaction)
        self.add_message_handler(BlockMessage, self.receive_block)
        self.add_message_handler(PeersMessage, self.receive_peers)

        # Use any number as seed
        random.seed(21)

    def started(self, id) -> None:
        logging.info('Community started')
        self.known_peers_mid.add(self.my_peer.mid)

        # Testing purpose
        # if id == 1:
        random_transaction_interval = random.randint(5, 10)
        self.register_task("tx_create", self.create_transaction, delay=7, interval=random_transaction_interval)

        random_check_interval = random.randint(5, 10)
        self.register_task("check_txs", self.block_creation, delay=7, interval=random_check_interval)

        self.register_task("send_peers", self.send_peers, delay=5)

    def peers_found(self):
        return len(self.get_peers()) > 0

    def get_peer_id(self, peer: Peer = None) -> str:
        return binascii.hexlify(peer.mid).decode()

    def create_transaction(self) -> None:
        if not self.peers_found():
            logging.info(f'[Node {self.get_peer_id(self.my_peer)}] No peers found')
            return

        # logging.info(f'[Node {self.get_peer_id(self.my_peer)}] Creating transaction')
        receiver_peer = random.choice([i for i in self.get_peers()])

        # Record the timestamp just before sending the transaction
        send_time = time.time()

        # ttl = 3 when creating a tx
        tx = Transaction(self.my_peer.mid, receiver_peer.mid, 10, nonce=self.counter)
        tx.public_key = self.crypto.key_to_bin(self.my_peer.key.pub())
        # should we sigh the hash of tx or the whole tx?
        tx.signature = self.crypto.create_signature(self.my_peer.key, tx.get_tx_bytes())
        # logging.info(
        #     f'[Node {self.get_peer_id(self.my_peer)}] Sending transaction {tx.nonce} to {self.get_peer_id(receiver_peer)}')
        self.pending_txs[tx.get_tx_hash()] = tx
        # and this is correct that initially we send this tx only to receiver?
        self.ez_send(receiver_peer, tx)
        self.counter += 1


    def block_creation(self):
        selected_peer_mid = random.choice(list(self.known_peers_mid))

        if not selected_peer_mid == self.my_peer.mid:
            return

        # logging.info(f'[Node {self.get_peer_id(self.my_peer)}] is creating a block')
        for tx_hash in list(self.pending_txs.keys()):
            tx = self.pending_txs.pop(tx_hash)
            self.finalized_txs[tx_hash] = tx
            self.current_block.add_transaction(tx)

            if self.current_block.is_full():
                logging.info(f'[Node {self.get_peer_id(self.my_peer)}] is creating a block {len(self.blocks)}')
                self.finalize_and_broadcast_block()
                break

    @lazy_wrapper(Transaction)
    async def on_transaction(self, peer: Peer, tx: Transaction) -> None:
        my_id = self.get_peer_id(self.my_peer)
        logging.info(f'[Node {my_id}] received transaction {tx.nonce} from {self.get_peer_id(peer)}')

        tx_hash = tx.get_tx_hash()
        # if we already have this tx we do nothing
        # here if we have the same txs received from different peers - we choose the one that was sent earlier?
        if tx_hash in self.finalized_txs or tx_hash in self.pending_txs:
            return

        # if the signature of tx is not valid we do nothing
        # todo need to get PublicKey object from bytes
        if not self.crypto.is_valid_signature(self.crypto.key_from_public_bin(tx.public_key), tx.get_tx_bytes(), tx.signature):
            logging.info(f'[Node {my_id}]: signature incorrect')
            return

        logging.info(f'[Node {my_id}]: signature correct')

         # Get the send time of the transaction
        # tx, send_time = self.pending_txs[tx_hash]
        # # Calculate the latency
        # latency = time.time() - send_time
        # logging.info(f'[Node {my_id}]: Latency for transaction {tx.nonce}: {latency} seconds')

        self.pending_txs[tx.get_tx_hash()] = tx
        if tx.ttl > 0:
            tx.ttl -= 1
            # push gossip to k random peers
            get_peers_to_distribute = random.sample(self.get_peers(), min(k, len(self.get_peers())))
            for peer in get_peers_to_distribute:
                self.ez_send(peer, tx)

    @lazy_wrapper(BlockMessage)
    async def receive_block(self, peer: Peer, payload: BlockMessage) -> None:
        logging.info('----------on block----------')

        # If the block is already our chain we do nothing
        if payload.hash in [block.get_merkle_hash() for block in self.blocks]:
            logging.info('block already known')

            return

        # Check block transactions and remove them from pending_txs list
        block_transactions = [self.serializer.unpack_serializable(Transaction, tx)[0] for tx in payload.block.transactions]
        new_balances = self.balances.copy()
        valid_txs = []

        for tx in block_transactions:
            tx_hash = tx.get_tx_hash()

            if new_balances[tx.sender] - tx.amount >= 0:
                new_balances[tx.sender] -= tx. amount
                new_balances[tx.receiver] += tx.amount

                if tx_hash in self.pending_txs:
                    self.pending_txs.pop(tx_hash)

                valid_txs.append(tx.get_tx_bytes())

        payload.block.set_transactions(valid_txs)
        self.balances = new_balances
        self.blocks.append(payload.block)

        if payload.ttl > 0:
            payload.ttl -= 1

            get_peers_to_distribute = random.sample(self.get_peers(), min(k, len(self.get_peers())))
            for peer in get_peers_to_distribute:
                self.ez_send(peer, payload)

    def finalize_and_broadcast_block(self):
        self.current_block.update_tree()
        new_block_hash = self.current_block.get_merkle_hash()
        # logging.info(f'New block hash: {new_block_hash}')
        self.blocks.append(self.current_block)

        self.broadcast_block(new_block_hash, self.current_block)
        self.current_block = Block(new_block_hash)

    def broadcast_block(self, block_hash: str, block: Block):
        blockMessage = BlockMessage(block_hash, block)

        for peer in self.get_peers():
            self.ez_send(peer, blockMessage)


    def send_peers(self) -> None:
        peers = self.get_peers()
        peerMessage = PeersMessage(self.my_peer.mid)

        for peer in peers:
            self.ez_send(peer, peerMessage)


    @lazy_wrapper(PeersMessage)
    def receive_peers(self, peer: Peer, payload: PeersMessage) -> None:
        if payload.mid not in self.known_peers_mid:

            self.known_peers_mid.add(payload.mid)

            peers = self.get_peers()
            peerMessage = PeersMessage(payload.mid, payload.ttl - 1)

            for peer in peers:
                self.ez_send(peer, peerMessage)

async def start_communities() -> None:
    # We create 7 peers
    for i in range(1,5):
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
