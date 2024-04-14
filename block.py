import hashlib

from merkle_tree import MerkleTree
import pickle


class Block:
    def __init__(self, previous_hash):
        self.previous_hash = previous_hash
        self.transactions = []
        self.merkle_tree = MerkleTree()

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        serialized_data = self.serialize(transaction)
        transaction_hash = hashlib.sha256(serialized_data).hexdigest()
        self.merkle_tree.add_leaf(transaction_hash)

    def is_full(self):
        return len(self.transactions) >= 10

    def serialize(self, transaction) -> bytes:
        return pickle.dumps({
            'sender': transaction.sender,
            'receiver': transaction.receiver,
            'amount': transaction.amount,
            'nonce': transaction.nonce,
            'ttl': transaction.ttl
        })