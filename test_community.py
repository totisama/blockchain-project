import time

from ipv8.test.base import TestBase
from ipv8.community import CommunitySettings

from collections import defaultdict

from block import Block
from blockchain import MyCommunity


class MyTests(TestBase[MyCommunity]):
    MAX_TEST_TIME = 120.0

    def setUp(self) -> None:
        super().setUp()

        self.COUNTER = 1
        self.MAX_MESSAGES = 5
        self.EXECUTED_CHECKS = 0
        self.PENDING_TXS = {}
        self.FINALIZED_TXS = {}
        self.BALANCES = defaultdict(lambda: 1000)
        self.BLOCKS = []
        self.CURRENT_BLOCK = Block('0')

    async def tearDown(self) -> None:
        await super().tearDown()

    async def test_initial_variables(self) -> None:
        self.initialize(MyCommunity, 1)
        overlay = self.overlay(0)

        counter = overlay.counter
        max_messages = overlay.max_messages
        executed_checks = overlay.executed_checks
        pending_txs = overlay.pending_txs
        finalized_txs = overlay.finalized_txs
        balances = overlay.balances
        blocks = overlay.blocks
        current_block = overlay.current_block

        self.assertEqual(self.COUNTER, counter)
        self.assertEqual(self.MAX_MESSAGES, max_messages)
        self.assertEqual(self.EXECUTED_CHECKS, executed_checks)
        self.assertEqual(self.PENDING_TXS, pending_txs)
        self.assertEqual(self.FINALIZED_TXS, finalized_txs)
        self.assertEqual(self.BALANCES, balances)
        self.assertEqual(self.BLOCKS, blocks)
        self.assertEqual(self.CURRENT_BLOCK.previous_hash, current_block.previous_hash)

    async def test_create_transaction(self) -> None:
        num_txs_overlay_1 = 10
        num_txs_overlay_2 = 10

        self.initialize(MyCommunity, 2)
        overlay1 = self.overlay(0)
        overlay2 = self.overlay(1)

        for _ in range(num_txs_overlay_1):
            overlay1.create_transaction()
        for _ in range(num_txs_overlay_2):
            overlay2.create_transaction()

        await self.deliver_messages()

        self.assertEqual(self.COUNTER + num_txs_overlay_1, overlay1.counter)
        self.assertEqual(self.COUNTER + num_txs_overlay_2, overlay2.counter)

    async def test_receive_transaction(self) -> None:
        num_txs_overlay_1 = 10
        num_txs_overlay_2 = 10

        self.initialize(MyCommunity, 2)
        overlay1 = self.overlay(0)
        overlay2 = self.overlay(1)

        for _ in range(num_txs_overlay_1):
            overlay1.create_transaction()
        for _ in range(num_txs_overlay_2):
            overlay2.create_transaction()

        await self.deliver_messages()

        self.assertEqual(num_txs_overlay_2 + num_txs_overlay_1, len(overlay1.pending_txs))
        self.assertEqual(num_txs_overlay_1 + num_txs_overlay_2, len(overlay2.pending_txs))

    async def test_gossip_transaction(self) -> None:
        num_txs_overlay_1 = 10
        num_txs_overlay_2 = 10

        self.initialize(MyCommunity, 3)
        overlay1 = self.overlay(0)
        overlay2 = self.overlay(1)
        overlay3 = self.overlay(2)

        for _ in range(num_txs_overlay_1):
            overlay1.create_transaction()

        await self.deliver_messages(1)

        for _ in range(num_txs_overlay_2):
            overlay2.create_transaction()

        await self.deliver_messages(1)

        total_txs = num_txs_overlay_1 + num_txs_overlay_2
        self.assertEqual(total_txs, len(overlay1.pending_txs))
        self.assertEqual(total_txs, len(overlay2.pending_txs))
        self.assertEqual(total_txs, len(overlay3.pending_txs))

    async def test_create_block(self) -> None:
        # Block gossip not yet implemented so this test doesn't pass at the moment
        num_txs_overlay_1 = 12
        num_txs_overlay_2 = 12

        self.initialize(MyCommunity, 3)
        overlay1 = self.overlay(0)
        overlay2 = self.overlay(1)
        overlay3 = self.overlay(2)

        for _ in range(num_txs_overlay_1):
            overlay1.create_transaction()
        for _ in range(num_txs_overlay_2):
            overlay2.create_transaction()

        await self.deliver_messages(1)

        overlay1.block_creation()
        overlay2.block_creation()

        await self.deliver_messages(1)

        num_blocks = int((num_txs_overlay_1 + num_txs_overlay_2) / 10)

        self.assertEqual(num_blocks, len(overlay1.blocks))
        self.assertEqual(num_blocks, len(overlay2.blocks))
        self.assertEqual(num_blocks, len(overlay3.blocks))

        self.assertEqual(num_txs_overlay_1 - (num_txs_overlay_1 % 10), len(overlay1.finalized_txs))
        self.assertEqual(num_txs_overlay_2 - (num_txs_overlay_2 % 10), len(overlay2.finalized_txs))
