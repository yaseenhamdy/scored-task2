# main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, String, select
import uvicorn
import os
import redis.asyncio as redis
import json

# --- Database Configuration ---
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

engine = create_async_engine(DATABASE_URL, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# --- Database Models ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)

# New Employee Model
class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)

# --- Database Setup ---
async def create_tables():
    async with engine.begin() as conn:
        # Base.metadata.create_all will create all tables defined from Base
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
        # async with takes care of closing the session automatically


# --- Redis Configuration ---
REDIS_URL = os.environ.get("REDIS_URL")
if not REDIS_URL:
     # Assuming Redis is critical for this setup
     raise ValueError("REDIS_URL environment variable not set")

redis_client: redis.Redis = None
CACHE_EXPIRY_SECONDS = 60 # Cache expiry time in seconds

# --- FastAPI Application ---
app = FastAPI()

# --- Application Lifecycle Events ---
@app.on_event("startup")
async def on_startup():
    print("Creating database tables...")
    # This will create both 'users' and 'employees' tables if they don't exist
    await create_tables()
    print("Database tables created (if they didn't exist).")

    print(f"Connecting to Redis at {REDIS_URL}...")
    global redis_client
    redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        await redis_client.ping()
        print("Connected to Redis successfully.")
    except redis.ConnectionError as e:
        print(f"Failed to connect to Redis: {e}")
        # Optionally raise an exception here if Redis is critical
        # raise Exception("Could not connect to Redis") from e

@app.on_event("shutdown")
async def on_shutdown():
    print("Closing database connection pool.")
    await engine.dispose()
    print("Closing Redis connection pool.")
    if redis_client:
        await redis_client.close()

# --- Endpoints ---
@app.get("/")
def read_root():
    return {"Hello": "World", "app_status": "running", "message": "Connected to FastAPI app."}

@app.get("/status")
def get_status():
    # This endpoint provides static status information, does not query DB/Redis
    return {
        "app_status": "running",
        "database_connection_status": "Configured via DATABASE_URL",
        "message": "Basic FastAPI app with DB and Redis setup."
    }

@app.get("/users/")
async def list_users(db: AsyncSession = Depends(get_db)):
    """
    List all users from the database, using Redis cache.
    """
    cache_key = "users:all"

    # 1. Try to read data from cache
    cached_users_json = await redis_client.get(cache_key)
    if cached_users_json:
        print(f"Cache hit for key: {cache_key}")
        return json.loads(cached_users_json)

    print(f"Cache miss for key: {cache_key}. Fetching from DB.")

    # 2. If data is not in cache, read it from the database
    result = await db.execute(select(User))
    users = result.scalars().all()

    # 3. Convert SQLAlchemy User objects to a list of dictionaries
    users_data = [{"id": user.id, "name": user.name, "email": user.email} for user in users]

    # 4. Store the data in the cache (after converting to JSON)
    users_json = json.dumps(users_data)
    await redis_client.set(cache_key, users_json, ex=CACHE_EXPIRY_SECONDS)
    print(f"Data stored in cache for key: {cache_key} with expiry: {CACHE_EXPIRY_SECONDS}s")

    # 5. Return the data fetched from the database
    return users_data

@app.post("/users/")
async def create_user(name: str, email: str, db: AsyncSession = Depends(get_db)):
    """
    Create a new user in the database.
    """
    db_user = User(name=name, email=email)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user) # Fetch the generated ID and any other fields

    # Invalidate the cache for the list of all users after creating a new one
    cache_key = "users:all"
    await redis_client.delete(cache_key)
    print(f"Cache invalidated for key: {cache_key}")

    # Return the data of the created user (converted to a dictionary)
    return {"id": db_user.id, "name": db_user.name, "email": db_user.email}

# --- New Endpoint for Employees ---
@app.get("/employees/")
async def list_employees(db: AsyncSession = Depends(get_db)):
    """
    List all employees from the database.
    (Note: This endpoint does not use caching in this example)
    """
    print("Fetching employees from DB.")
    result = await db.execute(select(Employee))
    employees = result.scalars().all()

    # Convert SQLAlchemy Employee objects to a list of dictionaries
    employees_data = [{"id": emp.id, "name": emp.name} for emp in employees]

    return employees_data


# The part for local execution is commented out as it's done in the Dockerfile's CMD
# if __name__ == "__main__":
#     uvicorn.run(app, host="0.0.0.0", port=80)