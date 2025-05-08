# seed_db.py
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

# استيراد الموديل من main.py
from main import Base, Employee, DATABASE_URL, AsyncSessionLocal, engine

async def seed_employees():
    """
    Adds some initial data to the employees table if it's empty.
    """
    if not DATABASE_URL:
         print("DATABASE_URL not set, cannot seed.")
         return

 
    current_engine = engine 
    CurrentAsyncSessionLocal = AsyncSessionLocal 


    async with CurrentAsyncSessionLocal() as db:
        print("Attempting to seed employees table...")
        try:
         
            count_result = await db.execute(select(Employee))
            existing_employees = count_result.scalars().all()

            if len(existing_employees) > 0:
                print(f"Employees table already contains {len(existing_employees)} records. Skipping seeding.")
                return

            # Add some employees
            employees_to_add = [
                Employee(name="Alice Smith"),
                Employee(name="Bob Johnson"),
                Employee(name="Charlie Brown"),
                Employee(name="David Lee"),
            ]

            db.add_all(employees_to_add)
            await db.commit()

            print(f"Successfully seeded employees table with {len(employees_to_add)} records.")

        except Exception as e:
            print(f"Error seeding employees: {e}")
            print("Attempting to create tables before seeding...")
            try:
                 async with current_engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
                 print("Tables created. Retrying seeding.")
                 await seed_employees() 
            except Exception as create_e:
                 print(f"Failed to create tables or re-seed: {create_e}")


if __name__ == "__main__":

    asyncio.run(seed_employees())
