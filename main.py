import os
from asyncio import run

from ipv8.community import Community, CommunitySettings
from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.lazy_community import lazy_wrapper
from ipv8.messaging.payload_dataclass import dataclass
from ipv8.types import Peer
from ipv8.util import run_forever
from ipv8_service import IPv8
import binascii
import hashlib
import random

letters = 'abcdefghijklmnopqrstuvwxyz'

@dataclass(msg_id=1)  # The value 1 identifies this message and must be unique per community
class Transaction:
    sender: int
    receiver: int
    amount: int
    data: str
    sign: bytes
    public_key: bytes

class MyCommunity(Community):
    community_id = b'harbourspaceuniverse'

    def __init__(self, settings: CommunitySettings) -> None:
      super().__init__(settings)
      self.string = self.getRandomString()

    def sendToPeers(self) -> None:
      print('sending to peers...')
      print(len(self.get_peers()), 'peers found')
      for peer in self.get_peers():
        if peer.mid == self.my_peer.mid:
          continue
        sign = self.crypto.create_signature(self.my_peer.key, self.string.encode())
        self.ez_send(peer, Transaction(1, 2, 10, self.string, sign, self.my_peer.public_key.key_to_bin()))

    def getRandomString(self) -> str:
      return ''.join(random.choice(letters) for _ in range(10))

    @lazy_wrapper(Transaction)
    def on_message(self, peer: Peer, payload: Transaction) -> None:
      print('received message')
      print('peer id: ', peer.mid)
      print(payload)
      if self.crypto.verify_signature(payload.public_key, payload.sign, self.string.encode()):
        print('signature is valid')
        data = {"sender": payload.sender, "receiver": payload.receiver, "amount": payload.amount}
      else:
        print('signature is invalid')

    def started(self) -> None:
      print('started')
      self.register_task("send_to_peers", self.sendToPeers, interval=5.0, delay=0)

async def start_communities() -> None:
  for i in [1, 2, 3, 4]:
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