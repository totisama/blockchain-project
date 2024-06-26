import binascii
import logging
import random as random
import random as random2
import sys

from collections import defaultdict
from datetime import time
from typing import Dict

from ipv8.community import Community, CommunitySettings
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.messaging.serialization import default_serializer
from ipv8.types import Peer

from block import Block
from block_request import BlockRequest, BlockResponse
from transaction import Transaction

# Amount of peers to send message to
k = 2

logfile = 'logfile.log'
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',handlers=[
        logging.StreamHandler(),  # Log to stdout
        logging.FileHandler(logfile, mode='w')  # Log to a file
    ])

@dataclass(msg_id=2)
class BlockMessage:
    hash: str
    block: Block
    ttl: int = 3
    signature: bytes = b''
    public_key: bytes = b''

    def get_block_bytes(self) -> bytes:
        return default_serializer.pack_serializable(self.block)


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
        # self.votes = { 'topic1': { 'yes': 0, 'no': 0 }, 'topic2': { 'yes': 0, 'no': 0 } }
        # self.voted = { 'peer1': { 'topic1': False, 'topic2': False }, 'peer2': { 'topic1': False, 'topic2': False }}
        self.votes = {}
        self.voted = {}

        self.pending_txs: Dict[str, Transaction] = {}
        self.finalized_txs: Dict[str, Transaction] = {}

        self.balances = defaultdict(lambda: 1000)
        self.blocks = []  # List to store finalized blocks
        self.current_block = Block('0')  # Current working block

        self.known_peers_mid = set()

        self.add_message_handler(Transaction, self.on_transaction)
        self.add_message_handler(BlockMessage, self.receive_block)
        self.add_message_handler(PeersMessage, self.receive_peers)
        self.add_message_handler(BlockRequest, self.on_block_request)
        self.add_message_handler(BlockResponse, self.on_block_response)

    def started(self) -> None:
        logging.info('Community started')
        self.known_peers_mid.add(self.my_peer.mid)

        # Testing purpose
        # if id == 1:
        # random_transaction_interval = random.randint(5, 10)
        # self.register_task("tx_create", self.create_transaction, delay=7, interval=random_transaction_interval)

        # random_check_interval = random.randint(5, 10)
        self.register_task("check_txs", self.block_creation, delay=7, interval=5)

        self.register_task("send_peers", self.send_peers, delay=5)

    def peers_found(self):
        return len(self.get_peers()) > 0

    def get_peer_id(self, peer: Peer = None) -> str:
        return binascii.hexlify(peer.mid).decode()

    def get_votes(self, topic: str) -> Dict:
        if topic in self.votes.keys():
            return self.votes[topic]
        return {"error": "Topic not found"}

    def create_transaction(self, topic: str = '', option: str = '') -> None:
        if not self.peers_found():
            logging.info(f'[Node {self.get_peer_id(self.my_peer)}] No peers found')
            return  {"error": "No peers found"}

        if not topic or not option:
            return {"error": "Missing information"}

        if self.my_peer.mid not in self.voted.keys():
            self.voted[self.my_peer.mid] = {}

        # If I already voted for this topic, I don't create a new transaction
        if topic in self.voted[self.my_peer.mid].keys():
            return {"error": "Already voted for this topic"}
        else:
            self.voted[self.my_peer.mid][topic] = True

        if topic not in self.votes.keys():
            self.votes[topic] = {}

        if option not in self.votes[topic].keys():
            self.votes[topic][option] = 0

        self.votes[topic][option] += 1

        # logging.info(f'[Node {self.get_peer_id(self.my_peer)}] Creating transaction')
        receiver_peer = random2.choice([i for i in self.get_peers()])

        # Record the timestamp just before sending the transaction
        # send_time = time.time()

        tx = Transaction(self.my_peer.mid, topic, option)
        tx.public_key = self.crypto.key_to_bin(self.my_peer.key.pub())
        tx.signature = self.crypto.create_signature(self.my_peer.key, tx.get_tx_bytes())
        self.pending_txs[tx.get_tx_hash()] = tx
        self.ez_send(receiver_peer, tx)
        self.counter += 1

        return self.votes[topic]

    def block_creation(self):
        # WIP: use hash of 2 or 3 previous block as seed
        random.seed(len(self.blocks))
        selected_peer_mid = random.choice(list(self.known_peers_mid))

        if not selected_peer_mid == self.my_peer.mid:
            return

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
        logging.info(f'[Node {my_id}] received transaction from {self.get_peer_id(peer)}')

        tx_hash = tx.get_tx_hash()
        # if we already have this tx we do nothing
        if tx_hash in self.finalized_txs or tx_hash in self.pending_txs:
            return

        # if the signature of tx is not valid we do nothing
        if not self.crypto.is_valid_signature(self.crypto.key_from_public_bin(tx.public_key), tx.get_tx_bytes(),
                                            tx.signature):
            logging.info(f'[Node {my_id}]: tx signature incorrect')
            return

        logging.info(f'[Node {my_id}]: tx signature correct')

        if tx.sender not in self.voted.keys():
            self.voted[tx.sender] = {}

        if tx.topic in self.voted[tx.sender].keys():
            return

        self.voted[tx.sender][tx.topic] = True

        if tx.topic not in self.votes.keys():
            self.votes[tx.topic] = {}

        if tx.vote not in self.votes[tx.topic].keys():
            self.votes[tx.topic][tx.vote] = 0

        self.votes[tx.topic][tx.vote] += 1

        self.pending_txs[tx_hash] = tx
        if tx.ttl > 0:
            tx.ttl -= 1
            # push gossip to k random peers
            get_peers_to_distribute = random2.sample(self.get_peers(), min(k, len(self.get_peers())))
            for peer in get_peers_to_distribute:
                self.ez_send(peer, tx)

    @lazy_wrapper(BlockRequest)
    async def on_block_request(self, peer: Peer, block_request: BlockRequest) -> None:
        my_id = self.get_peer_id(self.my_peer)
        logging.info(
            f'[Node {my_id}]: received block request with hash {block_request.block_hash} from {self.get_peer_id(peer)}')
        for block in self.blocks:
            if block.merkle_hash == block_request.block_hash:
                self.ez_send(peer, BlockResponse(block))

    @lazy_wrapper(BlockResponse)
    async def on_block_response(self, peer: Peer, block_response: BlockResponse) -> None:
        my_id = self.get_peer_id(self.my_peer)
        logging.info(
            f'[Node {my_id}]: received block response with hash {block_response.block.merkle_hash} from {self.get_peer_id(peer)}')
        for i, block in enumerate(self.blocks):
            if block.merkle_hash == block_response.block.previous_hash:
                self.blocks.insert(i + 1, block_response.block)
                return

    @lazy_wrapper(BlockMessage)
    async def receive_block(self, peer: Peer, payload: BlockMessage) -> None:
        logging.info(f'[Node {self.get_peer_id(self.my_peer)}] ----------on block----------')

        # stateless check
        my_id = self.get_peer_id(self.my_peer)
        if not self.crypto.is_valid_signature(self.crypto.key_from_public_bin(payload.public_key),
                                            payload.get_block_bytes(), payload.signature):
            logging.info(f'[Node {my_id}]: block signature incorrect')
            return
        logging.info(f'[Node {my_id}]: block signature correct')

        if payload.block.previous_hash not in [block.get_merkle_hash() for block in self.blocks]:
            logging.info(f'[Node {my_id}]: requesting prev block')
            # we don't know the prev block so we should request it
            self.ez_send(peer, BlockRequest(payload.block.previous_hash))
            return

        # stateful check
        # If the block is already in our chain we do nothing
        if payload.hash in [block.get_merkle_hash() for block in self.blocks]:
            logging.info(f'[Node {my_id}]: block already known')

            return

        # Check block transactions and remove them from pending_txs list
        block_transactions = [self.serializer.unpack_serializable(Transaction, tx)[0] for tx in
                            payload.block.transactions]

        # TODO: We should validate transactions at this point?
        for tx in block_transactions:
            tx_hash = tx.get_tx_hash()
            self.finalized_txs[tx_hash] = self.pending_txs.pop(tx_hash)

        self.blocks.append(payload.block)

        if payload.ttl > 0:
            payload.ttl -= 1

            get_peers_to_distribute = random2.sample(self.get_peers(), min(k, len(self.get_peers())))
            for peer in get_peers_to_distribute:
                self.ez_send(peer, payload)

    def finalize_and_broadcast_block(self):
        self.current_block.update_tree()
        new_block_hash = self.current_block.get_merkle_hash()
        # logging.info(f'New block hash: {new_block_hash}')
        # self.blocks.append(self.current_block)

        self.broadcast_block(new_block_hash, self.current_block)
        self.current_block = Block(new_block_hash)

    def broadcast_block(self, block_hash: str, block: Block):
        blockMessage = BlockMessage(block_hash, block)
        blockMessage.public_key = self.crypto.key_to_bin(self.my_peer.key.pub())
        # should we sigh the hash of tx or the whole tx?
        blockMessage.signature = self.crypto.create_signature(self.my_peer.key, blockMessage.get_block_bytes())

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

            self.known_peers_mid = set(sorted(list(self.known_peers_mid)))

            peers = self.get_peers()
            peerMessage = PeersMessage(payload.mid, payload.ttl - 1)

            for peer in peers:
                self.ez_send(peer, peerMessage)