from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import uvicorn

# Create web server
app = FastAPI()


@app.get("/get-transactions/{node_port}")
async def get_transactions(node_port: int):
    ipv8_instance = app.ipv8_instance
    transactions = ipv8_instance.overlays[0].finalized_txs
    print(transactions, len(transactions))

    if not ipv8_instance:
        raise HTTPException(status_code=404, detail="IPv8 instance not found")

    return {"status": "OK", "transactions-made": len(transactions)}

@app.get("/get-peers")
async def get_peers():
    ipv8_instance = app.ipv8_instance
    node = ipv8_instance.overlays[0]

    if not ipv8_instance:
        raise HTTPException(status_code=404, detail="IPv8 instance not found")

    return {"status": "OK", "number-of-peers": len(node.get_peers())}


@app.post("/send-message/{node_port}")
async def send_message(node_port: int):
    ipv8_instance = app.ipv8_instance

    print('IF YOU SEE THIS. THIS WORKED', ipv8_instance.overlays[0].counter)
    ipv8_instance.overlays[0].on_web_start()
    # ipv8_instance.overlays[0].start_client()

    if not ipv8_instance:
        raise HTTPException(status_code=404, detail="IPv8 instance not found")

    return {"status": "OK"}

    # Access the BlockchainNode community from your IPv8 instance
    blockchain_node = ipv8_instance.overlay[0]
    print(blockchain_node)

    if success:
        return {"status": "Transaction sent"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send transaction")


def run_web_server(ipv8_instance):
    app.ipv8_instance = ipv8_instance
    port = 8000

    while True:
        try:
            uvicorn.run(app, host="127.0.0.1", port=port)
            break  # If the server starts successfully, break the loop
        except OSError as e:
            if e.errno == 98:  # Error code for address already in use
                port += 1
            else:
                raise  # Reraises any other exception


if __name__ == "__main__":
    run_web_server()