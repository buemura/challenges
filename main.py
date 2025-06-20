from datetime import datetime

from fastapi import FastAPI, Request
import asyncio
import asyncpg
import json
from typing import AsyncIterator

app = FastAPI()
input_queue = asyncio.Queue()


# === Output stubs ===
async def write_to_db(pool, data):
    async with pool.acquire() as conn:
        # Convert timestamp to datetime object
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        await conn.execute(
            "INSERT INTO events(user_id, action, timestamp) VALUES($1, $2, $3)",
            data["user_id"], data["action"], timestamp
        )


async def publish_to_queue(data):
    # Simulate message queue publish (e.g., Kafka or RabbitMQ)
    print(f"Published to queue: {data}")


# === Generator for processing ===
async def event_streamer() -> AsyncIterator[dict]:
    while True:
        item = await input_queue.get()
        yield item
        input_queue.task_done()


# === Simple aggregator ===
async def aggregator(pool):
    user_action_count = {}  # Keep counts only, small memory
    async for event in event_streamer():
        uid = event["user_id"]
        user_action_count[uid] = user_action_count.get(uid, 0) + 1

        # Minimal in-memory aggregation
        event["action_count"] = user_action_count[uid]

        # Output
        await write_to_db(pool, event)
        await publish_to_queue(event)


# === Webhook endpoint ===
@app.post("/webhook")
async def receive_json(request: Request):
    data = await request.json()
    await input_queue.put(data)
    return {"status": "queued"}


# === Startup logic ===
@app.on_event("startup")
async def startup():
    app.state.db_pool = await asyncpg.create_pool(
        user='admin',  # or your actual username
        password='admin',
        database='data_pipeline',
        host='localhost'
    )
    asyncio.create_task(aggregator(app.state.db_pool))
