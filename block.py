import hashlib

from merkle_tree import MerkleTree
from ipv8.messaging.serialization import default_serializer
from ipv8.messaging.lazy_payload import VariablePayload
from ipv8.messaging.serialization import default_serializer

class Block(VariablePayload):
    format_list = ['varlenHutf8', 'varlenHutf8', 'varlenH-list']
    names = ['previous_hash', 'merkle_hash', 'transactions']

    def __init__(self, previous_hash: str = '', merkle_hash: str = '', transactions = []):
        self.previous_hash = str(previous_hash)
        self.transactions = transactions if len(transactions) > 0 else []
        self.merkle_tree = MerkleTree()
        self.merkle_hash = merkle_hash if merkle_hash != '' else ''

    def add_transaction(self, transaction):
        # We serialize the transaction before appending it to the array
        # because there seems to be an ipv8 problem when it tries to serialize the whole array
        serialized_transaction = default_serializer.pack_serializable(transaction)
        self.transactions.append(serialized_transaction)
        transaction_hash = hashlib.sha256(serialized_transaction).hexdigest()
        self.merkle_tree.add_leaf(transaction_hash)

    def is_full(self):
        return len(self.transactions) >= 10

    def update_tree(self):
        self.merkle_tree.recalculate_tree()
        self.merkle_hash = self.merkle_tree.get_root_hash()

    def get_merkle_hash(self) -> str:
        return self.merkle_hash