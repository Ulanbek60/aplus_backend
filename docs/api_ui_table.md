
---

# **API ↔ UI Mapping Table

APlus ERP — Specification**

Документ описывает, какие элементы интерфейса запрашивают какие API-эндпоинты, какие данные отображают и какие действия инициируют.

Используется всеми командами: backend, frontend, аналитики, QA.

---

# **1. Registration / Authentication Flow (Telegram Bot)**

| UI Step                         | API Endpoint                         | Method | Request                         | Response                        | Notes                                                |
| ------------------------------- | ------------------------------------ | ------ | ------------------------------- | ------------------------------- | ---------------------------------------------------- |
| User presses `/start`           | `/api/users/profile/<telegram_id>/`  | GET    | —                               | `{ status, role, ... }`         | Определяет новое ли устройство, нужна ли регистрация |
| Choose language                 | —                                    | —      | —                               | UI only                         | Bot controls state                                   |
| Submit name, surname, birthdate | —                                    | —      | —                               | —                               | Сохраняется локально до финала                       |
| Upload passport photos          | —                                    | —      | —                               | —                               | Validated by bot                                     |
| Upload license + selfie         | —                                    | —      | —                               | —                               | —                                                    |
| Choose vehicle type             | `/api/vehicles/`                     | GET    | —                               | `[ list of vehicles ]`          | Фронт бот показывает список типов                    |
| Final registration submit       | `/api/users/full_register/`          | POST   | user data + images + vehicle_id | `{ status: "ok" }`              | Создаёт User + VehicleRequest(pending)               |
| Pending approval screen         | `/api/users/profile/<id>/` (polling) | GET    | —                               | `{ status: "pending_vehicle" }` | Бот ждёт активации                                   |
| Admin approves                  | `/api/users/approve_vehicle/`        | POST   | telegram_id, vehicle_id         | `{status:"ok"}`                 | Меняет статус → active                               |
| Bot activates menu              | `/api/users/profile/<id>/`           | GET    | —                               | `{ status:"active" }`           | Показывает main menu                                 |

---

# **2. Main Menu (Driver)**

### Buttons:

* Start shift
* End shift
* Fuel
* Report issue
* Profile

| UI Action    | API                              | Method | Payload                               | Result                       |
| ------------ | -------------------------------- | ------ | ------------------------------------- | ---------------------------- |
| Start shift  | `/event → shift` via bot backend | POST   | `{ action: "start_shift", start_at }` | Creates shift event          |
| End shift    | same                             | POST   | `{ action: "end_shift", end_at }`     | Completes shift              |
| Fuel upload  | `/event → fuel`                  | POST   | `{ liters, photo }`                   | Saves refuel event           |
| Report issue | `/event → issue`                 | POST   | `{ description, photo }`              | Creates issue record         |
| View profile | `/api/users/profile/<tg>/`       | GET    | —                                     | Returns name, phone, vehicle |

---

# **3. Admin Panel — Vehicles List**

UI: Таблица всех машин

| UI Element         | API                          | Method    | Response                                             |
| ------------------ | ---------------------------- | --------- | ---------------------------------------------------- |
| Vehicles list page | `/api/vehicles/`             | GET       | `[{ id, name, type, lat, lon, fuel }]`               |
| Clicking a vehicle | `/api/vehicles/<id>/detail/` | GET       | `{ name, driver, mileage, fuel%, location, photos }` |
| Realtime updates   | `ws://.../ws/vehicles/`      | WebSocket | `{ vehicle_id, lat, lon, speed, fuel }`              |

---

# **4. Vehicle Detail Page**

Веб-приложение показывает карточку машины и реальное положение.

| UI Component        | API                          | Method | Notes                                |
| ------------------- | ---------------------------- | ------ | ------------------------------------ |
| Vehicle detail info | `/api/vehicles/<id>/detail/` | GET    | Полная информация                    |
| Track history       | `/api/vehicles/<id>/track/`  | GET    | Массив точек маршрута                |
| Events list         | `/api/vehicles/<id>/events/` | GET    | Открытия дверей, зажигание и т.п.    |
| Fuel history        | `/api/vehicles/<id>/fuel/`   | GET    | История топлива                      |
| Live updates        | `ws://.../ws/vehicles/<id>/` | WS     | Подписка только на конкретный veh_id |

---

# **5. Dashboard (Главный экран ERP)**

| Block               | API                        | Method | Description                                         |
| ------------------- | -------------------------- | ------ | --------------------------------------------------- |
| Statistics counters | `/api/vehicles/dashboard/` | GET    | Возвращает count_active, count_idle, count_low_fuel |
| Low fuel list       | same                       | GET    | part of response                                    |
| Idle vehicles       | same                       | GET    | part of response                                    |
| Active vehicles     | same                       | GET    | part of response                                    |

Формат ответа:

```json
{
  "stats": {
    "count_rented": 0,
    "count_repair": 0,
    "count_active": 12,
    "count_idle": 4,
    "count_low_fuel": 7
  },
  "active": ["..."],
  "idle": ["..."],
  "low_fuel": ["..."]
}
```

---

# **6. Administrative Vehicle Assignment**

(если используется вручную в панели)

| UI Action         | API                          | Method | Payload                       |
| ----------------- | ---------------------------- | ------ | ----------------------------- |
| Assign driver     | `/api/users/assign_vehicle/` | POST   | `{ telegram_id, vehicle_id }` |
| Admin login       | `/api/users/admin_login/`    | POST   | `{ username, password }`      |
| Remove assignment | (not implemented yet)        | —      | —                             |

---

# **7. WebSocket Architecture**

| Purpose               | Endpoint                         | Group          |
| --------------------- | -------------------------------- | -------------- |
| All vehicles realtime | `ws://.../ws/vehicles/`          | `vehicles`     |
| One vehicle realtime  | `ws://.../ws/vehicles/<veh_id>/` | `vehicle_<id>` |

Message format:

```json
{
  "vehicle_id": 3881,
  "lat": 42.87,
  "lon": 74.59,
  "speed": 34,
  "ignition": true,
  "fuel": 128.5,
  "ts": 1736258820
}
```

---

# **8. Pilot API Integration (internal)**


| Worker Action | Pilot Command   | Notes                                  |
| ------------- | --------------- | -------------------------------------- |
| Fetch status  | `status`        | Получение координат, топлива, скорости |
| List vehicles | `list`          | Первичная синхронизация                |
| Tracks        | `rungeo`        | История перемещений                    |
| Events        | `ag_events`     | События                                |
| Fuel history  | `sensorhistory` | Подробная история топлива              |

---

# **9. Summary Table: All API with Purpose**

| Endpoint                      | Method | Used by UI          | Description               |
| ----------------------------- | ------ | ------------------- | ------------------------- |
| `/api/users/full_register/`   | POST   | Telegram Bot        | Full registration         |
| `/api/users/profile/<id>/`    | GET    | Bot, UI             | User/profile info         |
| `/api/users/approve_vehicle/` | POST   | Admin               | Approve driver onboarding |
| `/api/users/assign_vehicle/`  | POST   | Admin               | Assign machine            |
| `/api/vehicles/`              | GET    | UI list             | List all vehicles         |
| `/api/vehicles/<id>/detail/`  | GET    | Vehicle detail page | Full machine info         |
| `/api/vehicles/<id>/status/`  | GET    | Debug, analytics    | Status history            |
| `/api/vehicles/<id>/track/`   | GET    | UI map              | Track points              |
| `/api/vehicles/<id>/events/`  | GET    | UI events panel     | Event log                 |
| `/api/vehicles/<id>/fuel/`    | GET    | UI fuel graph       | Fuel timeline             |
| `/api/vehicles/dashboard/`    | GET    | Dashboard           | Stats + quick lists       |
| `ws /ws/vehicles/`            | WS     | Map realtime        | All vehicles              |
| `ws /ws/vehicles/<id>/`       | WS     | Vehicle realtime    | Only one vehicle          |

---

