import asyncpg
from config import settings

async def get_db_connection():
    """
    Establish an asynchronous connection to the Neon PostgreSQL database.
    """
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        raise e

# Future: Add a connection pool if needed for higher scale
# pool = await asyncpg.create_pool(settings.DATABASE_URL)
