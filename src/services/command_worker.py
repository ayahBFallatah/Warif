"""
Background worker that reads queued device_commands and publishes to MQTT with retries.
Run: python -m src.services.command_worker
"""

import os
import time
import json
import logging
from datetime import datetime, timedelta
import psycopg2
import paho.mqtt.client as mqtt
from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        database=os.getenv("DB_NAME", "warif"),
        user=os.getenv("DB_USER", "warif_user"),
        password=os.getenv("DB_PASSWORD", "password"),
        port=os.getenv("DB_PORT", "5432"),
    )


def publish(device_id: str, command: dict) -> bool:
    broker_host = os.getenv("MQTT_BROKER", "localhost")
    broker_port = int(os.getenv("MQTT_PORT", "1883"))
    base = os.getenv("MQTT_CMD_BASE", "warif")
    topic = f"{base}/{device_id}/cmd"
    try:
        client = mqtt.Client()
        client.connect(broker_host, broker_port, 60)
        res = client.publish(topic, json.dumps(command), qos=1)
        res.wait_for_publish()
        client.disconnect()
        return res.rc == mqtt.MQTT_ERR_SUCCESS
    except Exception as e:
        logger.error(f"MQTT publish failed: {e}")
        return False


def run_loop(poll_seconds: int = 2, max_retries: int = 5):
    # start metrics server
    try:
        start_http_server(int(os.getenv("WORKER_METRICS_PORT", "9101")))
    except Exception as e:
        logger.warning(f"Metrics server failed to start: {e}")
    while True:
        try:
            conn = get_db_connection()
            with conn.cursor() as cursor:
                # Pick one queued or due command
                cursor.execute(
                    """
                    SELECT id, device_id, command
                    FROM device_commands
                    WHERE status IN ('queued','failed')
                      AND (next_attempt_at IS NULL OR next_attempt_at <= NOW())
                    ORDER BY created_at ASC
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
                if not row:
                    conn.commit()
                    conn.close()
                    time.sleep(poll_seconds)
                    continue

                cmd_id, device_id, command_json = row
                # Mark as sending attempt
                cursor.execute(
                    "UPDATE device_commands SET last_attempt_at = NOW() WHERE id = %s",
                    (cmd_id,),
                )
                conn.commit()

            # Publish outside the transaction to avoid long locks
            success = publish(device_id, command_json)

            with conn.cursor() as cursor:
                if success:
                    cursor.execute(
                        "UPDATE device_commands SET status='sent', response = %s WHERE id = %s",
                        (json.dumps({"published": True, "ts": datetime.utcnow().isoformat()}), cmd_id),
                    )
                else:
                    # increment retry, schedule next_attempt with backoff
                    cursor.execute(
                        """
                        UPDATE device_commands
                        SET status='failed', retry_count = retry_count + 1,
                            next_attempt_at = CASE WHEN retry_count + 1 >= %s THEN NULL ELSE NOW() + INTERVAL '30 seconds' * (retry_count + 1) END,
                            response = %s
                        WHERE id = %s
                        """,
                        (
                            max_retries,
                            json.dumps({"published": False, "error": "publish_failed", "ts": datetime.utcnow().isoformat()}),
                            cmd_id,
                        ),
                    )
                conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            try:
                conn.close()
            except Exception:
                pass
            time.sleep(poll_seconds)


if __name__ == "__main__":
    logger.info("Starting command worker...")
    run_loop()


