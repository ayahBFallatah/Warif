"""
Simple rules engine for Green Engine
Evaluates incoming sensor readings against configurable thresholds and writes alerts.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional
import logging
import os

import psycopg2


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ReadingContext:
    timestamp: datetime
    location: str
    sensor_type: str
    value: float


class RulesEngine:
    """Evaluates sensor readings against threshold rules and inserts alerts.

    Threshold precedence:
    1) system_config.config_key = 'sensor_thresholds' (JSONB map)
    2) built-in defaults
    """

    DEFAULT_THRESHOLDS: Dict[str, Dict[str, float]] = {
        "temperature": {"min": 10.0, "max": 35.0},
        "humidity": {"min": 30.0, "max": 90.0},
        "light": {"min": 0.0, "max": 2000.0},
        "soil_moisture": {"min": 10.0, "max": 90.0},
        "ec": {"min": 0.5, "max": 3.0},
        "co2": {"min": 300.0, "max": 2000.0},
    }

    def __init__(self):
        self._cached_thresholds: Optional[Dict[str, Dict[str, float]]] = None

    def _get_db_connection(self):
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            database=os.getenv("DB_NAME", "green_engine"),
            user=os.getenv("DB_USER", "green_user"),
            password=os.getenv("DB_PASSWORD", "password"),
            port=os.getenv("DB_PORT", "5432"),
        )

    def _load_thresholds_from_db(self) -> Optional[Dict[str, Dict[str, float]]]:
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT config_value
                    FROM system_config
                    WHERE config_key = 'sensor_thresholds' AND is_active = TRUE
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
                if row and row[0]:
                    return row[0]
        except Exception as e:
            logger.warning(f"Failed to load thresholds from DB, using defaults: {e}")
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass
        return None

    def get_thresholds(self) -> Dict[str, Dict[str, float]]:
        if self._cached_thresholds is None:
            db_thresholds = self._load_thresholds_from_db()
            self._cached_thresholds = db_thresholds or self.DEFAULT_THRESHOLDS
        return self._cached_thresholds

    def evaluate(self, reading: ReadingContext) -> Optional[Dict]:
        thresholds = self.get_thresholds().get(reading.sensor_type)
        if not thresholds:
            return None

        below_min = reading.value < thresholds.get("min", float("-inf"))
        above_max = reading.value > thresholds.get("max", float("inf"))

        if not (below_min or above_max):
            return None

        severity = "high" if above_max else "medium"
        title = (
            f"{reading.sensor_type.title()} above max"
            if above_max
            else f"{reading.sensor_type.title()} below min"
        )
        description = (
            f"{reading.sensor_type} reading {reading.value} at {reading.timestamp.isoformat()} "
            f"violated thresholds min={thresholds.get('min')} max={thresholds.get('max')}"
        )

        return {
            "timestamp": reading.timestamp,
            "location": reading.location,
            "alert_type": "threshold",
            "severity": severity,
            "title": title,
            "description": description,
            "sensor_id": None,
            "sensor_type": reading.sensor_type,
            "threshold_value": thresholds.get("max") if above_max else thresholds.get("min"),
            "actual_value": reading.value,
        }

    def insert_alert(self, alert: Dict) -> None:
        try:
            conn = self._get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO alerts (
                        timestamp, location, alert_type, severity,
                        title, description, sensor_id, sensor_type,
                        threshold_value, actual_value, status
                    ) VALUES (
                        %(timestamp)s, %(location)s, %(alert_type)s, %(severity)s,
                        %(title)s, %(description)s, %(sensor_id)s, %(sensor_type)s,
                        %(threshold_value)s, %(actual_value)s, 'active'
                    )
                    """,
                    alert,
                )
                conn.commit()
                # Slack notification
                try:
                    import requests
                    webhook = os.getenv("SLACK_WEBHOOK_URL")
                    if webhook:
                        msg = {
                            "text": f"[{alert.get('severity','').upper()}] {alert.get('title','')} at {alert.get('location','')}\n{alert.get('description','')}"
                        }
                        requests.post(webhook, json=msg, timeout=5)
                except Exception as se:
                    logger.warning(f"Slack notification failed: {se}")
        except Exception as e:
            logger.error(f"Failed to insert alert: {e}")
            raise
        finally:
            try:
                if conn:
                    conn.close()
            except Exception:
                pass

    def evaluate_and_store(self, reading: ReadingContext) -> Optional[Dict]:
        alert = self.evaluate(reading)
        if alert:
            self.insert_alert(alert)
        return alert


