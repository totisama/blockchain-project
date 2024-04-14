import hashlib

from merkle_tree import MerkleTree


class Block:
    def __init__(self):
        self.transactions = []
        self.merkle_tree = MerkleTree()

    def add_transaction(self, transaction):
        self.transactions.append(transaction)
        transaction_hash = hashlib.sha256(transaction.pack()).hexdigest()
        self.merkle_tree.add_leaf(transaction_hash)

    def is_full(self):
        return len(self.transactions) >= 10