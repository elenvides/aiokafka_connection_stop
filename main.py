"""Run limit order manager as module."""

import asyncio
import logging
import signal

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

logging.basicConfig(
    format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S', level=logging.INFO
)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVER_URI = "localhost:9096"
KAFKA_TRANSACTION_EXECUTOR_TOPIC = "testasyncname"
KAFKA_TRANSACTION_EXECUTOR_CONSUMER_GROUP_ID = "async_shutdown_group"


# region get producer and consumer data
async def check_producer_active(kafka_producer):
    test_topic = "testasyncname"
    test_message = "test_message"

    try:
        await kafka_producer.send(test_topic, test_message.encode('utf-8'))
        logger.info("==================== Producer is active")
    except Exception as e:
        logger.error(f"==================== Failed to send message with error: {e}. Producer might not be active.")


def get_active_consumer_groups():
    from kafka import KafkaAdminClient

    client = KafkaAdminClient(bootstrap_servers="localhost:9096")
    for group in client.list_consumer_groups():
        logger.info(f"==================== consumer group: {group[0]}")

    consumer_group_details = client.describe_consumer_groups(['async_shutdown_group'])
    for detail in consumer_group_details:
        logger.info(f"==================== consumer detail: {detail}")
# endregion get producer and consumer data


async def initialize_kafka():
    kafka_consumer = AIOKafkaConsumer(
        KAFKA_TRANSACTION_EXECUTOR_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVER_URI,
        group_id=KAFKA_TRANSACTION_EXECUTOR_CONSUMER_GROUP_ID,
        enable_auto_commit=True,
        auto_commit_interval_ms=1000,
        auto_offset_reset="latest",
    )

    kafka_producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVER_URI)

    await kafka_consumer.start()
    await kafka_producer.start()
    logger.info("==================== kafka initialized ")

    return kafka_consumer, kafka_producer


async def shutdown(kafka_consumer, kafka_producer):
    logger.info("==================== Connections closing started.......")
    await kafka_consumer.stop()
    await kafka_producer.stop()
    logger.info("==================== Connections closed.")


def setup_signal_handler(kafka_consumer, kafka_producer):
    logger.info("==================== setup_signal_handler ")
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGHUP, signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(kafka_consumer, kafka_producer)))


async def simulated_task(kafka_consumer, kafka_producer):
    logger.info("==================== simulated_task started")
    # Simulating some work
    await asyncio.sleep(5)
    logger.info("==================== simulated_task finished")


async def run_tasks():
    kafka_consumer, kafka_producer = await initialize_kafka()
    setup_signal_handler(kafka_consumer, kafka_producer)

    try:
        await simulated_task(kafka_consumer, kafka_producer)
    except Exception as e:
        logger.error(f"==================== Unexpected error: {e}")
    finally:
        logger.info("==================== finally")
        await shutdown(kafka_consumer, kafka_producer)


if __name__ == '__main__':
    asyncio.run(run_tasks())
