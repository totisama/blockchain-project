import hashlib

from merkle_tree import MerkleTree
from ipv8.messaging.serialization import default_serializer
from ipv8.messaging.lazy_payload import VariablePayload

class Block(VariablePayload):
    format_list = ['74s', '74s', 'payload-list']
    names = ['previous_hash', 'merkle_hash', 'transactions']

    def __init__(self, previous_hash: bytes = b''):
        self.previous_hash = previous_hash
        self.transactions = []
        self.merkle_tree = MerkleTree()
        self.merkle_hash = b''

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        serialized_data = default_serializer.pack_serializable(transaction)
        transaction_hash = hashlib.sha256(serialized_data).hexdigest()
        self.merkle_tree.add_leaf(transaction_hash)

    def is_full(self):
        return len(self.transactions) >= 2

    def update_tree(self):
        self.merkle_tree.recalculate_tree()
        self.merkle_hash = self.merkle_tree.get_root_hash()

    def get_merkle_hash(self) -> bytes:
        return self.merkle_hash