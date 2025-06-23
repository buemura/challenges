from datetime import datetime
from fastapi import FastAPI, Request
import asyncio
import asyncpg
import json
import os
from aio_pika import connect_robust, Message
from typing import AsyncIterator
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
input_queue = asyncio.Queue()


# Output: Write + Publish
async def write_to_db(pool, data):
    async with pool.acquire() as conn:
        timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        await conn.execute(
            "INSERT INTO events(user_id, action, timestamp) VALUES($1, $2, $3)",
            data["user_id"], data["action"], timestamp
        )


async def publish_to_queue(channel, data):
    body = json.dumps(data).encode()
    message = Message(body)
    await channel.default_exchange.publish(
        message,
        routing_key="events"  # the queue must be bound to this key
    )


# Generator
async def event_streamer() -> AsyncIterator[dict]:
    while True:
        item = await input_queue.get()
        yield item
        input_queue.task_done()


# Aggregator
async def aggregator(pool, channel):
    user_action_count = {}
    async for event in event_streamer():
        uid = event["user_id"]
        user_action_count[uid] = user_action_count.get(uid, 0) + 1
        event["action_count"] = user_action_count[uid]
        await write_to_db(pool, event)
        await publish_to_queue(channel, event)


# Webhook
@app.post("/webhook")
async def receive_json(request: Request):
    data = await request.json()
    await input_queue.put(data)
    return {"status": "queued"}


# Lifespan
@app.on_event("startup")
async def startup():
    # Load DB config
    db_pool = await asyncpg.create_pool(
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "admin"),
        database=os.getenv("DB_NAME", "data_pipeline"),
        host=os.getenv("DB_HOST", "localhost")
    )

    # Connect to RabbitMQ
    rabbit_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost/")
    connection = await connect_robust(rabbit_url)
    channel = await connection.channel()

    # Ensure the queue exists
    await channel.declare_queue("events", durable=True)

    # Start aggregator
    asyncio.create_task(aggregator(db_pool, channel))
