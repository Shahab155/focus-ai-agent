import asyncpg
from datetime import date
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
        titles = ", ".join([r['title'] for r in rows])
        raise ValueError(f"Multiple goals found: {titles}. Please be more specific.")

    return rows[0]['id']

async def update_tracking(user_id: str, goal_id: str = None, goal_title_query: str = None, metric_name: str = None, value: int = 0):
    """
    Update today's tracking record for a specific metric (action) of a goal.
    If the metric or today's log doesn't exist, they are created.
    """
    conn = await get_db_connection()
    try:
        resolved_id = await _resolve_goal_id(conn, user_id, goal_id, goal_title_query)
        if not resolved_id:
            return {"success": False, "message": "Goal not found. Please provide a valid ID or title."}

        async with conn.transaction():
            # 2. Get or create the metric (goal_action)
            action_id = await conn.fetchval(
                "SELECT id FROM goal_actions WHERE goal_id = $1 AND name = $2",
                resolved_id, metric_name
            )
            
            if not action_id:
                action_id = await conn.fetchval(
                    "INSERT INTO goal_actions (goal_id, name) VALUES ($1, $2) RETURNING id",
                    resolved_id, metric_name
                )

            # 3. Get or create today's daily log
            daily_log_id = await conn.fetchval(
                "SELECT id FROM daily_logs WHERE user_id = $1 AND date = $2",
                user_id, date.today()
            )
            
            if not daily_log_id:
                daily_log_id = await conn.fetchval(
                    "INSERT INTO daily_logs (user_id, date) VALUES ($1, $2) RETURNING id",
                    user_id, date.today()
                )

            # 4. Upsert action log
            await conn.execute(
                """
                INSERT INTO action_logs (daily_log_id, action_id, completed_value)
                VALUES ($1, $2, $3)
                ON CONFLICT (daily_log_id, action_id)
                DO UPDATE SET completed_value = EXCLUDED.completed_value
                """,
                daily_log_id, action_id, value
            )

        return {"success": True, "message": f"Updated {metric_name} to {value}"}
    except ValueError as e:
        return {"success": False, "message": str(e)}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()

async def get_today_tracking(user_id: str):
    """
    Fetch all tracking metrics for the user today.
    """
    conn = await get_db_connection()
    try:
        rows = await conn.fetch(
            """
            SELECT ga.name, al.completed_value, ga.goal_id
            FROM daily_logs dl
            JOIN action_logs al ON dl.id = al.daily_log_id
            JOIN goal_actions ga ON al.action_id = ga.id
            WHERE dl.user_id = $1 AND dl.date = $2
            """,
            user_id, date.today()
        )
        
        tracking_data = [
            {"metric": r['name'], "value": r['completed_value'], "goal_id": str(r['goal_id'])} 
            for r in rows
        ]
            
        return {"success": True, "data": tracking_data}
    except Exception as e:
        return {"success": False, "message": str(e)}
    finally:
        await conn.close()
