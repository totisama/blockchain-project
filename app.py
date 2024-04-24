import streamlit as st

from asyncio import run

from ipv8.configuration import ConfigBuilder, Strategy, WalkerDefinition, default_bootstrap_defs
from ipv8_service import IPv8

from blockchain import MyCommunity


async def create_community():
    builder = ConfigBuilder().clear_keys().clear_overlays()
    builder.add_key("my peer", "medium", f"ec{7}.pem")
    builder.add_overlay("MyCommunity", "my peer",
                        [WalkerDefinition(Strategy.RandomWalk,
                                          10, {'timeout': 3.0})],
                        default_bootstrap_defs, {}, [('started', 7)])
    ipv8_instance = IPv8(builder.finalize(),
                         extra_communities={'MyCommunity': MyCommunity})
    return ipv8_instance


async def start_community(ipv8_instance):
    await ipv8_instance.start()


ipv8_instance = run(create_community())
run(start_community(ipv8_instance))
community = ipv8_instance.overlays[0]


def create_transaction():
    tx = community.create_transaction()
    if tx is not None:
        st.write(tx.sender)


st.write("""
# Test app
""")

st.button("Create transaction", on_click=create_transaction)
