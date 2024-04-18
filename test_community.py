from main import MyCommunity
from ipv8.test.base import TestBase

class MyTests(TestBase[MyCommunity]):

    def setUp(self) -> None:
        super().setUp()
        # Insert your setUp logic here

    async def tearDown(self) -> None:
        await super().tearDown()
        # Insert your tearDown logic here

    async def test_call(self) -> None:
        self.initialize(MyCommunity, 1)

        # Nodes are 0-indexed
        value = self.overlay(0).