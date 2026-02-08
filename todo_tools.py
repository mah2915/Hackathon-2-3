"""
MCP tool definitions for todo operations.
Uses OpenAI function calling format for tool definitions.
"""
from typing import Optional, List, Dict, Any
from uuid import UUID
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.todo import Todo


# Tool Definitions (OpenAI function calling format)

CREATE_TODO_TOOL = {
    "type": "function",
    "function": {
        "name": "create_todo",
        "description": "Create a new todo item for the user",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title or summary of the todo item"
                },
                "description": {
                    "type": "string",
                    "description": "Optional detailed description of the todo item"
                }
            },
            "required": ["title"]
        }
    }
}

LIST_TODOS_TOOL = {
    "type": "function",
    "function": {
        "name": "list_todos",
        "description": "List all todo items for the user, optionally filtered by completion status",
        "parameters": {
            "type": "object",
            "properties": {
                "completed": {
                    "type": "boolean",
                    "description": "Filter by completion status. If not provided, returns all todos."
                }
            },
            "required": []
        }
    }
}

UPDATE_TODO_TOOL = {
    "type": "function",
    "function": {
        "name": "update_todo",
        "description": "Update a todo item's title, description, or completion status",
        "parameters": {
            "type": "object",
            "properties": {
                "todo_id": {
                    "type": "string",
                    "description": "The UUID of the todo item to update"
                },
                "title": {
                    "type": "string",
                    "description": "New title for the todo item"
                },
                "description": {
                    "type": "string",
                    "description": "New description for the todo item"
                },
                "completed": {
                    "type": "boolean",
                    "description": "New completion status"
                }
            },
            "required": ["todo_id"]
        }
    }
}

DELETE_TODO_TOOL = {
    "type": "function",
    "function": {
        "name": "delete_todo",
        "description": "Delete a todo item",
        "parameters": {
            "type": "object",
            "properties": {
                "todo_id": {
                    "type": "string",
                    "description": "The UUID of the todo item to delete"
                }
            },
            "required": ["todo_id"]
        }
    }
}

GET_TODO_TOOL = {
    "type": "function",
    "function": {
        "name": "get_todo",
        "description": "Get details of a specific todo item",
        "parameters": {
            "type": "object",
            "properties": {
                "todo_id": {
                    "type": "string",
                    "description": "The UUID of the todo item to retrieve"
                }
            },
            "required": ["todo_id"]
        }
    }
}

# All tools list for easy registration
ALL_TOOLS = [
    CREATE_TODO_TOOL,
    LIST_TODOS_TOOL,
    UPDATE_TODO_TOOL,
    DELETE_TODO_TOOL,
    GET_TODO_TOOL
]


# Tool Handler Functions

async def create_todo_handler(
    session: AsyncSession,
    user_id: UUID,
    title: str,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Handler for create_todo tool.

    Args:
        session: Database session
        user_id: UUID of the user creating the todo
        title: Todo title
        description: Optional todo description

    Returns:
        Dict with success status and todo details
    """
    try:
        todo = Todo(
            user_id=user_id,
            title=title,
            description=description,
            completed=False
        )
        session.add(todo)
        await session.commit()
        await session.refresh(todo)

        return {
            "success": True,
            "todo_id": str(todo.id),
            "title": todo.title,
            "description": todo.description,
            "completed": todo.completed
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create todo: {str(e)}"
        }


async def list_todos_handler(
    session: AsyncSession,
    user_id: UUID,
    completed: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Handler for list_todos tool.

    Args:
        session: Database session
        user_id: UUID of the user
        completed: Optional filter by completion status

    Returns:
        Dict with success status and list of todos
    """
    try:
        statement = select(Todo).where(Todo.user_id == user_id)

        if completed is not None:
            statement = statement.where(Todo.completed == completed)

        statement = statement.order_by(Todo.created_at.desc())

        result = await session.execute(statement)
        todos = result.scalars().all()

        return {
            "success": True,
            "todos": [
                {
                    "id": str(todo.id),
                    "title": todo.title,
                    "description": todo.description,
                    "completed": todo.completed,
                    "created_at": todo.created_at.isoformat()
                }
                for todo in todos
            ],
            "count": len(todos)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list todos: {str(e)}"
        }


async def update_todo_handler(
    session: AsyncSession,
    user_id: UUID,
    todo_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    completed: Optional[bool] = None
) -> Dict[str, Any]:
    """
    Handler for update_todo tool.

    Args:
        session: Database session
        user_id: UUID of the user
        todo_id: UUID string of the todo to update
        title: Optional new title
        description: Optional new description
        completed: Optional new completion status

    Returns:
        Dict with success status and updated todo details
    """
    try:
        todo_uuid = UUID(todo_id)
        statement = select(Todo).where(
            Todo.id == todo_uuid,
            Todo.user_id == user_id
        )
        result = await session.execute(statement)
        todo = result.scalar_one_or_none()

        if not todo:
            return {
                "success": False,
                "error": "Todo not found or you don't have permission to update it"
            }

        # Update fields if provided
        if title is not None:
            todo.title = title
        if description is not None:
            todo.description = description
        if completed is not None:
            todo.completed = completed

        session.add(todo)
        await session.commit()
        await session.refresh(todo)

        return {
            "success": True,
            "todo_id": str(todo.id),
            "title": todo.title,
            "description": todo.description,
            "completed": todo.completed
        }
    except ValueError:
        return {
            "success": False,
            "error": "Invalid todo ID format"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update todo: {str(e)}"
        }


async def delete_todo_handler(
    session: AsyncSession,
    user_id: UUID,
    todo_id: str
) -> Dict[str, Any]:
    """
    Handler for delete_todo tool.

    Args:
        session: Database session
        user_id: UUID of the user
        todo_id: UUID string of the todo to delete

    Returns:
        Dict with success status
    """
    try:
        todo_uuid = UUID(todo_id)
        statement = select(Todo).where(
            Todo.id == todo_uuid,
            Todo.user_id == user_id
        )
        result = await session.execute(statement)
        todo = result.scalar_one_or_none()

        if not todo:
            return {
                "success": False,
                "error": "Todo not found or you don't have permission to delete it"
            }

        await session.delete(todo)
        await session.commit()

        return {
            "success": True,
            "message": f"Todo '{todo.title}' deleted successfully"
        }
    except ValueError:
        return {
            "success": False,
            "error": "Invalid todo ID format"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to delete todo: {str(e)}"
        }


async def get_todo_handler(
    session: AsyncSession,
    user_id: UUID,
    todo_id: str
) -> Dict[str, Any]:
    """
    Handler for get_todo tool.

    Args:
        session: Database session
        user_id: UUID of the user
        todo_id: UUID string of the todo to retrieve

    Returns:
        Dict with success status and todo details
    """
    try:
        todo_uuid = UUID(todo_id)
        statement = select(Todo).where(
            Todo.id == todo_uuid,
            Todo.user_id == user_id
        )
        result = await session.execute(statement)
        todo = result.scalar_one_or_none()

        if not todo:
            return {
                "success": False,
                "error": "Todo not found or you don't have permission to view it"
            }

        return {
            "success": True,
            "todo": {
                "id": str(todo.id),
                "title": todo.title,
                "description": todo.description,
                "completed": todo.completed,
                "created_at": todo.created_at.isoformat(),
                "updated_at": todo.updated_at.isoformat()
            }
        }
    except ValueError:
        return {
            "success": False,
            "error": "Invalid todo ID format"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to get todo: {str(e)}"
        }
