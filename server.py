from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import uvicorn

# Create web server
app = FastAPI()

@app.get("/get-peers")
async def get_peers():
    ipv8_instance = app.ipv8_instance
    node = ipv8_instance.overlays[0]

    if not ipv8_instance:
        raise HTTPException(status_code=404, detail="IPv8 instance not found")

    return {"status": "OK", "number-of-peers": len(node.get_peers())}

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