from fastapi import FastAPI, HTTPException
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

@app.get("/vote/{topic}/{vote}")
async def send_vote(topic: str, vote: str):
    ipv8_instance = app.ipv8_instance

    if not ipv8_instance:
        return {"status_code": 404, "error": "IPv8 instance not found", "reponse": {}}

    node = ipv8_instance.overlays[0]

    reponse = node.create_transaction(topic, vote)

    if reponse is None:
        return {"status_code": 401, "error": "There was a problem sending the vote. Please try again later.", "reponse": {}}

    if "error" in reponse.keys():
        return {"status_code": 401, "error": reponse["error"], "reponse": {}}

    return {"status_code": 200, "status": "OK", "response": reponse}

@app.get("/votes/{topic}")
async def get_topic_votes(topic: str):
    ipv8_instance = app.ipv8_instance

    if not ipv8_instance:
        return {"status_code": 404, "error": "IPv8 instance not found", "reponse": {}}

    node = ipv8_instance.overlays[0]

    reponse = node.get_votes(topic)

    if reponse is None:
        return {"status_code": 401, "error": "There was a problem sending the vote. Please try again later.", "reponse": {}}

    if "error" in reponse.keys():
        return {"status_code": 401, "error": reponse["error"], "reponse": {}}

    return {"status_code": 200, "status": "OK", "response": reponse}

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