import os
from asyncio import run

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import dataclass
from collections import defaultdict
from ipv8.types import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8
import binascii
import hashlib
import random

letters = 'abcdefghijklmnopqrstuvwxyz'

@dataclass(msg_id=1)  # The value 1 identifies this message and must be unique per community
class Transaction:
    sender: bytes
    receiver: bytes
    amount: int
    nonce: int = 1

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

    def started(self) -> None:
      print('started')
      self.register_task("tx_create", self.create_transaction, delay=1, interval=5)

    def peers_found(self):
      return len(self.get_peers()) > 0

    def get_peer_id(self, peer: Peer =None):
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

        # if self.counter > self.max_messages:
        #     self.cancel_pending_task("tx_create")
        #     self.stop()
        #     return

    @message_wrapper(Transaction)
    async def on_message(self, peer: Peer, payload: Transaction) -> None:

        # Add to pending transactions
        if (payload.sender, payload.nonce) not in [(tx.sender, tx.nonce) for tx in self.finalized_txs] and (
        payload.sender, payload.nonce) not in [(tx.sender, tx.nonce) for tx in self.pending_txs]:
            self.pending_txs.append(payload)

        # Gossip to other nodes
        # WIP: Implement correct gossiping
        # for peer in [i for i in self.get_peers() if self.node_id_from_peer(i) % 2 == 1]:
        for peer in self.get_peers():
            self.ez_send(peer, payload)

async def start_communities() -> None:
  for i in [1, 2]:
    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("my peer", "medium", f"ec{i}.pem")
    builder.add_overlay("MyCommunity", "my peer",
      [WalkerDefinition(Strategy.RandomWalk,
                        10, {'timeout': 3.0})],
      default_bootstrap_defs, {}, [('started',)])
    await IPv8(builder.finalize(),
      extra_communities={'MyCommunity': MyCommunity}).start()
  await run_forever()


run(start_communities())