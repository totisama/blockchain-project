import threading

from asyncio import run

from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8_service import IPv8
from ipv8.util import run_forever

from blockchain import MyCommunity
from server import run_web_server

async def start_community():
    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("my peer", "medium", f"ec{7}.pem")
    builder.add_overlay("MyCommunity", "my peer",
                        [WalkerDefinition(Strategy.RandomWalk,
                                          10, {'timeout': 3.0})],
                        default_bootstrap_defs, {}, [('started', )])
    ipv8_instance = IPv8(builder.finalize(),
                         extra_communities={'MyCommunity': MyCommunity})

    await ipv8_instance.start()
    fastapi_thread = threading.Thread(target=lambda: run_web_server(ipv8_instance))
    fastapi_thread.start()
    await run_forever()


run(start_community())
