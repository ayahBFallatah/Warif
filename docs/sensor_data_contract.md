# Warif Sensor Data Contract

## Purpose
This document defines the unified sensor measurement structure used across:
- historical data ingestion
- real-time sensor ingestion
- digital twin state generation
- dashboard visualization

## Current Ingestion Model
The current backend ingests sensor data as one measurement per record.
Each record represents a single sensor reading for one sensor type at one timestamp.

## Unified Fields

| Field | Type | Required | Unit | Description |
|------|------|----------|------|-------------|
| timestamp | datetime | yes | ISO 8601 | Reading timestamp |
| sensor_id | string | yes | - | Unique sensor/device identifier |
| location | string | yes | - | Farm zone, tray, or greenhouse section |
| sensor_type | string | yes | - | Type of measurement (e.g. soil_moisture, temperature, humidity) |
| value | float | yes | depends | Sensor reading value |
| unit | string | yes | depends | Measurement unit |
| battery | int | no | % | Device battery level |
| signal_strength | int | no | dBm | Device signal strength |

## Supported Sensor Types
- temperature
- humidity
- light
- soil_moisture
- ec
- co2

## Notes
- One row = one sensor measurement
- Multiple measurements at the same timestamp are stored as separate rows
- Digital Twin current state must be built by grouping latest records by location + sensor_type

## Validation Rules
- timestamp must be valid ISO 8601 datetime
- sensor_type must be one of the supported sensor types
- value must be numeric
- battery is optional and should be between 0 and 100
- signal_strength is optional and should be between -100 and 0