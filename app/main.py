from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"response": "Server is running. Get /docs to see the endpoints."}
