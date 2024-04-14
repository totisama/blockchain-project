import binascii
import random
from asyncio import run
from collections import defaultdict

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


@dataclass(msg_id=1)  # The value 1 identifies this message and must be unique per community
class Transaction:
    sender: bytes
    receiver: bytes
    amount: int
    nonce: int = 1
    ttl: int = 3


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
        self.current_block = Block()  # Current working block

        self.add_message_handler(Transaction, self.on_transaction)

    def started(self, id) -> None:
        print('started')
        # Testing purpose
        if id == 1:
            self.register_task("tx_create", self.create_transaction, delay=1, interval=5)
        # WIP: Check if this is the right way to check transactions
        self.register_task("check_txs", self.check_transactions, delay=1, interval=7)

    def peers_found(self):
        return len(self.get_peers()) > 0

    def get_peer_id(self, peer: Peer = None):
        return binascii.hexlify(peer.mid).decode()

    def create_transaction(self):
        if not self.peers_found():
            print(f'[Node {self.get_peer_id(self.my_peer)}] No peers found')
            return

        print(f'[Node {self.get_peer_id(self.my_peer)}] Creating transaction')
        peer = random.choice([i for i in self.get_peers()])
        peer_id = peer.mid

        tx = Transaction(self.my_peer.mid,
                         peer_id,
                         10,
                         self.counter)
        self.counter += 1
        print(f'[Node {self.get_peer_id(self.my_peer)}] Sending transaction {tx.nonce} to {self.get_peer_id(peer)}')
        self.ez_send(peer, tx)

        # WIP: We need this?
        # if self.counter > self.max_messages:
        #     self.cancel_pending_task("tx_create")
        #     self.stop()
        #     return

    def check_transactions(self):
        for tx in self.pending_txs:
            if self.balances[tx.sender] - tx.amount >= 0:
                self.balances[tx.sender] -= tx.amount
                self.balances[tx.receiver] += tx.amount
                self.pending_txs.remove(tx)
                self.finalized_txs.append(tx)

        self.executed_checks += 1
        # WIP: Create block

        # WIP: We need this?
        # if self.executed_checks > 10:
        #     self.cancel_pending_task("check_txs")
        #     print(self.balances)
        #     self.stop()

    @lazy_wrapper(Transaction)
    async def on_transaction(self, peer: Peer, payload: Transaction) -> None:
        my_id = self.get_peer_id(self.my_peer)

        print(f'[Node {my_id}] Received transaction', payload.nonce, 'from', self.get_peer_id(peer))

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

        self.current_block.add_transaction(payload)
        if self.current_block.is_full():
            self.finalize_and_broadcast_block()

    def finalize_and_broadcast_block(self):
        self.current_block.merkle_tree.recalculate_tree()
        new_block_hash = self.current_block.merkle_tree.get_root_hash()
        print(f'New block hash: {new_block_hash}')
        self.blocks.append(self.current_block)
        self.current_block = Block()

        self.broadcast_new_block(new_block_hash)

    def broadcast_new_block(self, block_hash):
        for peer in self.get_peers():
            self.ez_send(peer, block_hash)


async def start_communities() -> None:
    # We create 7 peers
    for i in range(1, 8):
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
