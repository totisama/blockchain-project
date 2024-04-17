from hashlib import sha256

from ipv8.messaging.payload_dataclass import dataclass
from ipv8.messaging.serialization import default_serializer


@dataclass(msg_id=1)  # The value 1 identifies this message and must be unique per community
class Transaction:
    sender: bytes
    receiver: bytes
    amount: int
    nonce: int = 1
    ttl: int = 3
    signature: bytes = b''
    public_key: bytes = b''

    def get_tx_bytes(self) -> bytes:
        tx_copy = Transaction(self.sender, self.receiver, self.amount, self.nonce)
        return default_serializer.pack_serializable(tx_copy)

    def get_tx_hash(self) -> bytes:
        return sha256(self.get_tx_bytes()).digest()