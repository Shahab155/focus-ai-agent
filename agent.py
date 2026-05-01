from typing import Optional
from pydantic import BaseModel
from agents import Agent, Runner, function_tool, OpenAIChatCompletionsModel, AsyncOpenAI
from agents.tool_context import ToolContext
from dotenv import load_dotenv
import os

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

model = OpenAIChatCompletionsModel(openai_client=client, model=os.getenv("MODEL"))

# Import tools
from tools.goals import create_goal, update_goal, delete_goal, complete_goal, get_goals
from tools.journal import write_journal, update_journal, get_today_journal
from tools.tracking import update_tracking, get_today_tracking
from tools.avoid_list import add_avoid_item, mark_avoid_completed, delete_avoid_item

# 1. Define Context Model for User-Specific Data
class AgentContext(BaseModel):
    user_id: str

# 2. Define Function Tool Wrappers

@function_tool
async def get_goals_tool(ctx: ToolContext[AgentContext]):
    """Retrieve all goals for the user, including their IDs and titles."""
    return await get_goals(ctx.context.user_id)

@function_tool
async def create_goal_tool(ctx: ToolContext[AgentContext], title: str, description: Optional[str] = None):
    """Create a new goal for the user. Max 3 active goals allowed."""
    return await create_goal(ctx.context.user_id, title, description)

@function_tool
async def update_goal_tool(ctx: ToolContext[AgentContext], goal_id: Optional[str] = None, title_query: Optional[str] = None, title: Optional[str] = None, description: Optional[str] = None, progress: Optional[int] = None):
    """
    Update an existing goal. 
    Provide either 'goal_id' or a 'title_query' to identify the goal.
    Update 'title', 'description', or 'progress' (0-100).
    """
    return await update_goal(ctx.context.user_id, goal_id, title_query, title, description, progress)

@function_tool
async def delete_goal_tool(ctx: ToolContext[AgentContext], goal_id: Optional[str] = None, title_query: Optional[str] = None):
    """
    Delete a goal. 
    Provide either 'goal_id' or a 'title_query' (e.g., part of the goal title) to identify the goal.
    """
    return await delete_goal(ctx.context.user_id, goal_id, title_query)

@function_tool
async def complete_goal_tool(ctx: ToolContext[AgentContext], goal_id: Optional[str] = None, title_query: Optional[str] = None):
    """
    Mark a goal as completed.
    Provide either 'goal_id' or a 'title_query' to identify the goal.
    """
    return await complete_goal(ctx.context.user_id, goal_id, title_query)

@function_tool
async def write_journal_tool(ctx: ToolContext[AgentContext], content: str, mood: Optional[str] = None):
    """Save a journal entry for today. Optional mood can be included."""
    return await write_journal(ctx.context.user_id, content, mood)

@function_tool
async def update_journal_tool(ctx: ToolContext[AgentContext], entry_id: str, content: str):
    """Update the content of a specific journal entry."""
    return await update_journal(ctx.context.user_id, entry_id, content)

@function_tool
async def get_today_journal_tool(ctx: ToolContext[AgentContext]):
    """Retrieve the user's journal entry for today."""
    return await get_today_journal(ctx.context.user_id)

@function_tool
async def update_tracking_tool(ctx: ToolContext[AgentContext], goal_id: Optional[str] = None, goal_title_query: Optional[str] = None, metric_name: str = "", value: int = 0):
    """
    Log daily progress for a specific metric (e.g., 'applications', 'minutes').
    Provide either 'goal_id' or 'goal_title_query' to link the metric to a goal.
    """
    return await update_tracking(ctx.context.user_id, goal_id, goal_title_query, metric_name, value)

@function_tool
async def get_today_tracking_tool(ctx: ToolContext[AgentContext]):
    """Get all progress logs recorded for today."""
    return await get_today_tracking(ctx.context.user_id)

@function_tool
async def add_avoid_item_tool(ctx: ToolContext[AgentContext], title: str):
    """Add a new item to the 'Things to Avoid' list."""
    return await add_avoid_item(ctx.context.user_id, title)

@function_tool
async def mark_avoid_completed_tool(ctx: ToolContext[AgentContext], item_id: str, avoided: bool = True):
    """Mark whether an avoid item was successfully avoided today."""
    return await mark_avoid_completed(ctx.context.user_id, item_id, avoided)

@function_tool
async def delete_avoid_item_tool(ctx: ToolContext[AgentContext], item_id: str):
    """Remove an item from the avoid list."""
    return await delete_avoid_item(ctx.context.user_id, item_id)

# 3. Create the Agent Brain
agent = Agent(
    name="Focus App AI Assistant",
    instructions="""
    You are the Focus App AI Assistant. Your goal is to help users manage their productivity effectively.
    
    You assist with:
    - Managing Goals (max 3 active goals).
    - Writing and updating Daily Journals.
    - Tracking daily progress metrics linked to goals.
    - Managing a 'Things to Avoid' list.
    
    Guidelines:
    - Be concise, practical, and helpful.
    - IMPORTANT: You can update, delete, or complete goals using either their ID or by searching for their TITLE.
    - If a user mentions a goal by name (e.g., "delete my Get job goal"), use the 'title_query' parameter in the corresponding tool.
    - If you are unsure which goal the user means, use 'get_goals_tool' to see their current list and then ask for clarification.
    - Whenever a user asks to change or log data, use the appropriate tool.
    - Never guess or assume success if a tool call fails; report the tool's response.
    - Always use the provided tools to ensure data is scoped correctly to the user.
    """,
    model=model,
    tools=[
        get_goals_tool, create_goal_tool, update_goal_tool, delete_goal_tool, complete_goal_tool,
        write_journal_tool, update_journal_tool, get_today_journal_tool,
        update_tracking_tool, get_today_tracking_tool,
        add_avoid_item_tool, mark_avoid_completed_tool, delete_avoid_item_tool
    ]
)

# 4. Main Process Function
async def process_message(user_id: str, message: str):
    """
    Main entry point for processing user messages.
    """
    try:
        context = AgentContext(user_id=user_id)
        result = await Runner.run(agent, message, context=context)
        return {"reply": result.final_output}
    except Exception as e:
        print(f"Agent Error: {e}")
        return {"reply": "I'm sorry, I encountered an error while processing your request."}

async def run_agent(message: str, user_id: str):
    return await process_message(user_id, message)
