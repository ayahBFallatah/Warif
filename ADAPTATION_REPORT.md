#  :  Green Engine  Warif
## Warif Backend Adaptation Report

---

##  :   (Green Engine)

###   Green Engine

** template**  GitHub         **   (Microgreens)**.

###  :

```
GREEN ENGINE ORIGINAL SYSTEM
 Backend (FastAPI + PostgreSQL + MQTT)
    Sensor ingestion (MQTT   )
    Real-time alerts (   )
    ML models (   +   )
    Database (sensor_readings, growth_measurements, alerts)
    Prometheus monitoring ( )
 Streamlit Dashboard (  -)
 MQTT Broker (Mosquitto)
 Docker Compose ( )

 :      
```

---

##  :  Warif

  :

> "Irrigation management is the most critical and immediate challenge farmers face"

###  Warif:
-  **Real-time environmental monitoring** (   )
-  **Machine learning-based irrigation prediction** (  )
-  **Recommendation generation** ( )
-  **Dashboard visualization** ( Show)

###    :
-  Microgreens-specific features ( )
-  Plant height/biomass tracking (  )
-  Harvest predictions ( )
-  3D visualization  simulation (  )

---

##  :    Green Engine 

### 1.   (Architecture)
```
 :
  - FastAPI  web framework
  - PostgreSQL + TimescaleDB  
  - MQTT    
  - JWT authentication
  - Role-based access control (RBAC)
  - Prometheus metrics
```

### 2.    (Data Pipeline)
```
 :
  MQTT broker  Sensor ingestion  Feature engineering  Storage  API

  File:
  - src/ingestion/mqtt_client.py (  MQTT)
  - src/etl/feature_engineering.py ( )
  - src/utils/rules_engine.py (  )
```

### 3.  ML (Machine Learning)
```
  (  ):
  - Anomaly detection (    )
  - Time series forecasting (  )
  
  File:
  - src/models/anomaly_detection.py
  - src/models/forecasting_models.py
  - src/models/train_models.py
```

### 4.  
```
  ( ):
  - Alert engine   
  -     
  
  File:
  - src/utils/rules_engine.py
```

### 5.   (Device Control)
```
 :
  -   MQTT  pumps, fans, lights
  - Queue system  (background worker)
  
  File:
  - src/services/command_worker.py
  - API endpoints: POST /api/v1/commands
```

---

##  :     

### 1.   / 

```
 :
  ai_models/              (  )
  chatbot/                (chatbot    )
  digital_twin/           (   digital twin)
  iot/                   
  backend/ (Node.js)    Node.js  + Python  

:    
```

### 2.  File  

```
 :
  fix_green_engine.py, fix_auth.py       
  dashboard_local.py                      dashboard/app.py
  scripts/mqtt_ingestion_client.py       src/ingestion/mqtt_client.py
  scripts/demo_phase7-10.py               
  start_green_engine.sh, fixed.sh        start_warif.sh

:    
```

### 3.   

```
 :
  timescaledb==0.0.1   requirements.txt

: 
  -    (TimescaleDB  extension  PostgreSQL  Python package)
  -      Render
  - psycopg2    PostgreSQL/TimescaleDB

:  build failure
```

### 4. Streamlit Dashboard (    )

```
    :
  dashboard/app.py     

: 
  - Warif  React frontend (warif.netlify.app)  Streamlit
  - Streamlit      
```

---

##  :    Warif 

### 1. Rebrand 

```
 :
  "Green Engine"  "Warif"           ( File)
  "green_engine"  "warif"           (database, MQTT topics)
  "greenengine/"  "warif/"          (MQTT topic base)

:   
```

### 2. CORS  Frontend Integration

```
 :
  CORS middleware  src/api/main.py
  
  :
    allow_origins=["*"]  ( )
  
  :
    allow_origins = [  CORS_ORIGINS env var]
    default: https://warif.netlify.app

:   React - 
```

### 3. render.yaml  

```
 :
  render.yaml
  
   :
  - pythonVersion: "3.11.0"
  - autoDeploy: true
  - healthCheckPath: /health
  - CORS_ORIGINS configuration

:    Render
```

### 4. Frontend API Service Layer

```
  (  ):
  src/services/api.js        ( )
  src/hooks/useSensorData.js (React hooks)
  
   :  React    

:   -  
```

---

##  :  

|  |  |  |  |
|--------|--------|---------|--------|
| **Real-time Monitoring** |  MQTT ingestion |    |  ready |
| **Sensor Data** |  Generic sensors |    |  ready |
| **Irrigation Control** |  Device commands |    |  ready |
| **Alerts** |  Rules engine |    |  ready |
| **Predictions (ML)** |  Prophet/XGBoost |    |  ready |
| **Authentication** |  JWT |    |  ready |
| **Dashboard** | Streamlit |  React  |    |
| **Database** | PostgreSQL |   |  ready |
| **Simulation** |    |     |   2 |
| **Chatbot** |   |     |   2 |

---

##  :  

###    Green Engine:
 **80%**    

- Architecture  (FastAPI + PostgreSQL + MQTT)
- Data pipeline (MQTT  Feature engineering  DB)
- ML models (Forecasting + Anomaly detection)
- API structure  endpoints
- Authentication system (JWT + RBAC)
- Device control system
- Alert engine

###  /:
 **15%**    Warif

- Rebranding (Green Engine  Warif)
- Removed microgreen-specific features
- Removed empty/placeholder folders
- Removed broken/duplicate files
- Fixed timescaledb dependency
- CORS configuration for React frontend
- Cleanup and organization

###  :
 **5%**   

- render.yaml (deployment config)
- Frontend service layer (api.js)
- React hooks (useSensorData)
- start_warif.sh script
- ADAPTATION_REPORT.md (this document)

---

## 

**Green Engine**  template    .  ** **  ( )   **Warif**     (microgreen-specific)  ** ** (React frontend).

**:**  ready  digital twin        simulation  chatbot.

---

*     11  2026*
*Prepared with Claude Code*
