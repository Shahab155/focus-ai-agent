import asyncpg
from datetime import date
from db import get_db_connection

async def add_avoid_item(user_id: str, title: str):
    """
    Add a new item to the user's 'Things to Avoid' list.
    """
    conn = await get_db_connection()
    try:
        await conn.execute(
            "INSERT INTO avoid_items (user_id, name) VALUES ($1, $2)",
            user_id, title
        )
        return {"success": True, "message": f"Added '{title}' to avoid list"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

async def mark_avoid_completed(user_id: str, item_id: str, avoided: bool = True):
    """
    Mark an avoid item as successfully avoided (or not) for today.
    """
    conn = await get_db_connection()
    try:
        # Check if item belongs to user
        item_exists = await conn.fetchval(
            "SELECT 1 FROM avoid_items WHERE id = $1 AND user_id = $2",
            item_id, user_id
        )
        if not item_exists:
            return {"success": False, "message": "Avoid item not found or does not belong to user"}

        # Upsert into avoid_logs
        await conn.execute(
            """
            INSERT INTO avoid_logs (user_id, avoid_item_id, date, avoided)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id, avoid_item_id, date)
            DO UPDATE SET avoided = EXCLUDED.avoided
            """,
            user_id, item_id, date.today(), avoided
        )
        status = "avoided" if avoided else "not avoided"
        return {"success": True, "message": f"Marked item as {status} for today"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

async def delete_avoid_item(user_id: str, item_id: str):
    """
    Delete an item from the avoid list.
    """
    conn = await get_db_connection()
    try:
        result = await conn.execute(
            "DELETE FROM avoid_items WHERE id = $1 AND user_id = $2",
            item_id, user_id
        )
        
        if result == "DELETE 0":
            return {"success": False, "message": "Item not found or does not belong to user"}
            
        return {"success": True, "message": "Avoid item deleted successfully"}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

# --- Testing Helpers ---
# if __name__ == "__main__":
#     import asyncio
#     async def test():
#         res = await add_avoid_item("user-uuid", "Social Media")
#         print(res)
#     asyncio.run(test())
