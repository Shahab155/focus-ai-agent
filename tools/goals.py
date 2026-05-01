import asyncpg
from datetime import datetime
from db import get_db_connection
from typing import Optional

async def _resolve_goal_id(conn, user_id: str, goal_id: Optional[str] = None, title_query: Optional[str] = None):
    """
    Helper to find a goal ID by either direct ID or a title search.
    """
    if goal_id:
        return goal_id
    
    if not title_query:
        return None

    # Search for the goal by title (case-insensitive, partial match)
    rows = await conn.fetch(
        "SELECT id, title FROM goals WHERE user_id = $1 AND title ILIKE $2",
        user_id, f"%{title_query}%"
    )

    if not rows:
        return None
    
    if len(rows) > 1:
        # If multiple matches, we can't decide automatically
        # Returning a list of titles might help the agent clarify
        titles = ", ".join([r['title'] for r in rows])
        raise ValueError(f"Multiple goals found: {titles}. Please be more specific.")

    return rows[0]['id']

async def get_goals(user_id: str):
    """
    Retrieve all goals for the user.
    """
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            "SELECT id, title, description, completed, progress, created_at FROM goals WHERE user_id = $1 ORDER BY created_at DESC",
            user_id
        )
        return {
            "success": True,
            "data": [dict(r) for r in rows]
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

async def create_goal(user_id: str, title: str, description: str = None):
    """
    Insert a new goal for the user. Respects the max 3 active goals rule.
    """
    conn = await get_db_connection()
    try:
        # Check active goals count
        count = await conn.fetchval(
            "SELECT COUNT(*) FROM goals WHERE user_id = $1 AND completed = FALSE",
            user_id
        )
        
        if count >= 3:
            return {
                "success": False,
                "message": "User already has 3 active goals. Complete or delete one to add more."
            }
        
        # Insert new goal
        await conn.execute(
            """
            INSERT INTO goals (user_id, title, description, created_at, completed, progress)
            VALUES ($1, $2, $3, $4, FALSE, 0)
            """,
            user_id, title, description, datetime.utcnow()
        )
        
        return {
            "success": True,
            "message": f"Goal '{title}' created successfully"
        }
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

async def update_goal(user_id: str, goal_id: str = None, title_query: str = None, title: str = None, description: str = None, progress: int = None):
    """
    Update a goal identified by ID or title query.
    """
    conn = await get_db_connection()
    try:
        resolved_id = await _resolve_goal_id(conn, user_id, goal_id, title_query)
        if not resolved_id:
            return {"success": False, "message": "Goal not found. Please provide a valid ID or title."}

        # Build dynamic update query
        fields = []
        values = []
        counter = 1
        
        if title is not None:
            fields.append(f"title = ${counter}")
            values.append(title)
            counter += 1
        if description is not None:
            fields.append(f"description = ${counter}")
            values.append(description)
            counter += 1
        if progress is not None:
            fields.append(f"progress = ${counter}")
            values.append(progress)
            counter += 1
            
        if not fields:
            return {"success": False, "message": "No fields provided for update"}
            
        # Add resolved_id and user_id to the query
        query = f"UPDATE goals SET {', '.join(fields)} WHERE id = ${counter} AND user_id = ${counter + 1}"
        values.extend([resolved_id, user_id])
        
        result = await conn.execute(query, *values)
        
        if result == "UPDATE 0":
            return {"success": False, "message": "Goal not found or does not belong to user"}
            
        return {"success": True, "message": "Goal updated successfully"}
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

async def delete_goal(user_id: str, goal_id: str = None, title_query: str = None):
    """
    Delete a goal identified by ID or title query.
    """
    conn = await get_db_connection()
    try:
        resolved_id = await _resolve_goal_id(conn, user_id, goal_id, title_query)
        if not resolved_id:
            return {"success": False, "message": "Goal not found. Please provide a valid ID or title."}

        result = await conn.execute(
            "DELETE FROM goals WHERE id = $1 AND user_id = $2",
            resolved_id, user_id
        )
        
        if result == "DELETE 0":
            return {"success": False, "message": "Goal not found or does not belong to user"}
            
        return {"success": True, "message": "Goal deleted successfully"}
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

async def complete_goal(user_id: str, goal_id: str = None, title_query: str = None):
    """
    Mark a goal identified by ID or title query as completed.
    """
    conn = await get_db_connection()
    try:
        resolved_id = await _resolve_goal_id(conn, user_id, goal_id, title_query)
        if not resolved_id:
            return {"success": False, "message": "Goal not found. Please provide a valid ID or title."}

        result = await conn.execute(
            "UPDATE goals SET completed = TRUE, progress = 100 WHERE id = $1 AND user_id = $2",
            resolved_id, user_id
        )
        
        if result == "UPDATE 0":
            return {"success": False, "message": "Goal not found or does not belong to user"}
            
        return {"success": True, "message": "Goal marked as completed"}
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()
