import asyncpg
from datetime import date
from db import get_db_connection

async def write_journal(user_id: str, content: str, mood: str = None):
    """
    Insert today's journal entry. Uses an upsert logic if an entry already exists for today.
    """
    conn = await get_db_connection()
    try:
        # Using ON CONFLICT because journal_entries has UNIQUE(user_id, date)
        await conn.execute(
            """
            INSERT INTO journal_entries (user_id, content, date, mood)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, date) 
            DO UPDATE SET content = EXCLUDED.content, mood = EXCLUDED.mood
            """,
            user_id, content, date.today(), mood
        )
        return {"success": True, "message": "Journal entry saved successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

async def update_journal(user_id: str, entry_id: str, content: str):
    """
    Update a specific journal entry content.
    """
    conn = await get_db_connection()
    try:
        result = await conn.execute(
            "UPDATE journal_entries SET content = $1 WHERE id = $2 AND user_id = $3",
            content, entry_id, user_id
        )
        
        if result == "UPDATE 0":
            return {"success": False, "message": "Entry not found or does not belong to user"}
            
        return {"success": True, "message": "Journal entry updated successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

async def get_today_journal(user_id: str):
    """
    Fetch today's journal entry for the user.
    """
    conn = await get_db_connection()
    try:
        row = await conn.fetchrow(
            "SELECT id, content, mood, date FROM journal_entries WHERE user_id = $1 AND date = $2",
            user_id, date.today()
        )
        
        if not row:
            return {"success": False, "message": "No entry found for today"}
            
        return {
            "success": True, 
            "data": {
                "id": str(row['id']),
                "content": row['content'],
                "mood": row['mood'],
                "date": str(row['date'])
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

# --- Testing Helpers ---
# if __name__ == "__main__":
#     import asyncio
#     async def test():
#         res = await write_journal("some-uuid", "Feeling productive today!", "Happy")
#         print(res)
#     asyncio.run(test())
