from typing import List

from ipv8.messaging.lazy_payload import VariablePayload

from merkle_tree import MerkleTree
from transaction import Transaction


class Block(VariablePayload):
    format_list = ['varlenHutf8', 'varlenHutf8', 'varlenH-list']
    names = ['previous_hash', 'merkle_hash', 'transactions']

    def __init__(self, previous_hash: str = '', merkle_hash: str = None, transactions: List[bytes] = None):
        # super().__init__()
        self.previous_hash = previous_hash
        self.transactions = [] if transactions is None else transactions
        self.merkle_tree = MerkleTree()
        self.merkle_hash = '' if merkle_hash is None else merkle_hash

    def add_transaction(self, transaction: Transaction):
        # We serialize the transaction before appending it to the array
        # because there seems to be an ipv8 problem when it tries to serialize the whole array
        self.transactions.append(transaction.get_tx_bytes())
        self.merkle_tree.add_leaf(transaction.get_tx_hash())

    def set_transactions(self, transactions: List[bytes]):
        self.transactions = transactions

    def is_full(self) -> bool:
        return len(self.transactions) >= 5

    def update_tree(self):
        self.merkle_tree.recalculate_tree()
        self.merkle_hash = self.merkle_tree.get_root_hash()

    def get_merkle_hash(self) -> str:
        return self.merkle_hash
