# Stage 1: Data Persistence & API Design Assessment

A production-ready FastAPI service that aggregates demographic data from three external sources (**Genderize**, **Agify**, and **Nationalize**) and persists the results in an external PostgreSQL database. 

## 🌟 Key Features
* **API Aggregation**: Simultaneously fetches data from three upstream APIs using asynchronous concurrency.
* **Data Persistence**: Stores processed profiles in a managed PostgreSQL database.
* **Idempotency**: Prevents duplicate records; returns existing data if a name has already been processed.
* **Smart Filtering**: Advanced GET endpoint with optional, case-insensitive query parameters.
* **UUID v7**: Utilizes time-ordered Version 7 UUIDs for optimized database indexing and sorting.
* **Robust Error Handling**: Implements strict 502 Bad Gateway rules for upstream data gaps.

## 🏗️ Tech Stack
* **Framework**: FastAPI
* **Database**: PostgreSQL (External)
* **ORM**: SQLAlchemy
* **Concurrency**: Asyncio + HTTPX
* **Deployment**: Vercel

## 📂 API Reference

### 1. Create Profile
`POST /api/profiles`
* **Body**: `{ "name": "ella" }`
* **Logic**: Aggregates data, classifies age groups, and determines the most likely country.
* **Idempotency**: Returns `201 Created` for new names or `200 OK` with a "Profile already exists" message for duplicates.

### 2. Get Profile by ID
`GET /api/profiles/{id}`
* Returns the full demographic profile for a specific UUID.

### 3. List & Filter Profiles
`GET /api/profiles?gender=male&country_id=NG&age_group=adult`
* Supports optional filters.
* Returns a count of results and an array of profile objects.

### 4. Delete Profile
`DELETE /api/profiles/{id}`
* Permanently removes a record (204 No Content).

## 🗄️ Database Schema & Logic

| Field | Source / Rule |
| :--- | :--- |
| `id` | Generated UUID v7 (Time-ordered) |
| `age_group` | Classified: Child (0-12), Teen (13-19), Adult (20-59), Senior (60+) |
| `country_id` | Top result from Nationalize API |
| `created_at` | UTC ISO 8601 Timestamp |

## 🚀 Local Setup

1.  **Clone & Install**:
    ```bash
    git clone https://github.com/Sevenwings26/HNG_Stage1-Data-Persistence-API-Design-Assessment/tree/main

    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file in the root:
    ```env
    DATABASE_URL=postgresql://user:password@hostname:5432/dbname
    ```

3.  **Run**:
    ```bash
    uvicorn api.main:app --reload
    ```

## ⚠️ Edge Case Handling (502 Bad Gateway)
To ensure data integrity, the API will **not** store a profile if:
* Genderize returns `null` or `0` count.
* Agify returns a `null` age.
* Nationalize returns no country data.

---

### Pro-Tip for Submission
In your repository, make sure you include a `vercel.json` and a `requirements.txt` containing:
* `fastapi`
* `uvicorn`
* `sqlalchemy`
* `psycopg2-binary` (or `asyncpg`)
* `httpx`
* `uuid-utils`
* `python-dotenv`



