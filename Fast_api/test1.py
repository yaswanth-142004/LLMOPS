import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://yaswanth:mysecurepass@localhost:5432/bookly_db"

async def test_connection():
    try:
        engine = create_async_engine(DATABASE_URL, echo=True)
        async with engine.begin() as conn:
            result = await conn.execute("SELECT version();")
            print("✅ Connected:", result.fetchall())
    except Exception as e:
        print("❌ Connection failed:", e)

asyncio.run(test_connection())
