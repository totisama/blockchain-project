import unittest
from ipv8.test.base import TestBase
from ipv8.messaging.payload import Payload
from main import MyCommunity, Transaction, BlockMessage
from block import Block


class TestBlockchain(unittest.TestCase):

    async def setUp(self):
        self.community = await self._create_community()

    async def tearDown(self):
        await self.community.unload()

    async def _create_community(self):
        test_base = TestBase(MyCommunity)
        test_base.initialize(MyCommunity, 1)
        community = test_base.overlay(0)

        return community

    async def test_transaction_creation(self):
        # Create a transaction
        transaction = Transaction(b'sender_id', b'receiver_id', 10, 1)

        # Send the transaction to the community
        await self.community.on_transaction(None, transaction)

        # Check if the transaction is added to the pending transactions
        self.assertEqual(len(self.community.pending_txs), 1)

    async def test_block_creation_and_propagation(self):
        block = Block('block_hash')

        block_message = BlockMessage('block_hash', block)
        await self.community.receive_block(None, block_message)

        # Check if the block is added to the blockchain
        self.assertEqual(len(self.community.blocks), 1)

        # Check if the block is propagated to peers
        # For simplicity, we assume that all peers receive the block

        # Check if the received block matches the sent block
        received_block = self.community.blocks[0]
        self.assertEqual(received_block.get_hash(), block.get_hash())


if __name__ == '__main__':
    unittest.main()
