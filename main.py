from asyncio import run

from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8.util import run_forever
from ipv8_service import IPv8

from blockchain import MyCommunity

async def start_communities() -> None:
    # We create 7 peers
    for i in range(1,5):
        builder = ConfigBuilder().clear_keys().clear_overlays()
        builder.add_key("my peer", "medium", f"ec{i}.pem")
        builder.add_overlay("MyCommunity", "my peer",
                            [WalkerDefinition(Strategy.RandomWalk,
                                            10, {'timeout': 3.0})],
                            default_bootstrap_defs, {}, [('started', i)])
        await IPv8(builder.finalize(),
                extra_communities={'MyCommunity': MyCommunity}).start()
    await run_forever()


run(start_communities())
