from datetime import datetime
from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import asyncio
import asyncpg
import json
import os
from aio_pika import connect_robust, Message
from typing import AsyncIterator, Union
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
input_queue = asyncio.Queue(maxsize=10000)  # large buffer for burst tolerance


# Output: Write to DB + Publish to MQ
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
        message, routing_key="events"
    )


# Event Generator
async def event_streamer() -> AsyncIterator[dict]:
    while True:
        event = await input_queue.get()
        yield event
        input_queue.task_done()


# Aggregator / Transformer
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
    payload = await request.body()

    # Parse and stream items regardless of batch size
    def parse_json_stream() -> Union[dict, list]:
        parsed = json.loads(payload)
        if isinstance(parsed, dict):
            return [parsed]
        elif isinstance(parsed, list):
            return parsed
        else:
            raise ValueError("Invalid JSON format")

    for item in parse_json_stream():
        await input_queue.put(item)

    return {"status": "queued", "received": len(parse_json_stream())}


# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # DB setup
    db_pool = await asyncpg.create_pool(
        user=os.getenv("DB_USER", "admin"),
        password=os.getenv("DB_PASSWORD", "admin"),
        database=os.getenv("DB_NAME", "data_pipeline"),
        host=os.getenv("DB_HOST", "localhost")
    )

    # RabbitMQ setup
    rabbit_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq/")
    connection = await connect_robust(rabbit_url)
    channel = await connection.channel()
    await channel.declare_queue("events", durable=True)

    # Run aggregator task
    task = asyncio.create_task(aggregator(db_pool, channel))

    yield

    task.cancel()
    await db_pool.close()
    await connection.close()


app.router.lifespan_context = lifespan
