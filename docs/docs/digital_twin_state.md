# Warif Digital Twin Current State

## Purpose
This document defines how the current digital twin state is derived from sensor measurements stored in the database.

## Concept
The current digital twin state is not stored as a separate object.
It is computed dynamically from the latest available sensor readings for each location.

## Current State Logic
For each location:
- retrieve the latest reading for each sensor_type
- combine these readings into one current state snapshot
- use this snapshot to represent the current environmental condition of that location

## Supported Sensor Types
- temperature
- humidity
- light
- soil_moisture
- ec
- co2

## Output Example
{
  "location": "greenhouse_a",
  "last_update": "2026-04-15T12:00:00Z",
  "temperature": 24.5,
  "humidity": 62.1,
  "light": 430.0,
  "soil_moisture": 35.8,
  "ec": 1.7,
  "co2": 650.0,
  "status": "normal"
}

## Status Rules
- normal → كل القيم طبيعية
- warning → قيمة قريبة من الحد
- critical → قيمة خطرة

## Notes
- كل صف في DB = قراءة واحدة
- لازم نجمع آخر القيم لكل sensor_type عشان نكوّن الحالة