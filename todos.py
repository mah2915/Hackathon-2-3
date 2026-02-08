"""
Todo routes for CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from uuid import UUID
from datetime import datetime
from typing import List
from app.database import get_session
from app.schemas.todo import TodoCreate, TodoUpdate, TodoResponse
from app.models.todo import Todo
from app.models.user import User
from app.auth.dependencies import get_current_user
from app.utils.responses import success_response, error_response


router = APIRouter()


@router.post("/users/{user_id}/todos", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_todo(
    user_id: UUID,
    todo_data: TodoCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new todo item for the authenticated user.

    Args:
        user_id: User ID from URL path (must match authenticated user)
        todo_data: Todo creation data (title and optional description)
        current_user: Authenticated user from JWT token
        session: Database session

    Returns:
        Success response with created todo data

    Raises:
        HTTPException: 403 if user_id doesn't match authenticated user
    """
    # Verify user_id in path matches authenticated user
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="FORBIDDEN",
                message="You can only create todos for yourself"
            )
        )

    # Create new todo
    new_todo = Todo(
        user_id=current_user.id,
        title=todo_data.title,
        description=todo_data.description
    )

    session.add(new_todo)
    await session.commit()
    await session.refresh(new_todo)

    # Convert to response model
    todo_response = TodoResponse.model_validate(new_todo)

    return success_response(
        data=todo_response.model_dump(),
        message="Todo created successfully"
    )


@router.get("/users/{user_id}/todos", response_model=dict)
async def list_todos(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    List all todos for the authenticated user.

    Args:
        user_id: User ID from URL path (must match authenticated user)
        current_user: Authenticated user from JWT token
        session: Database session

    Returns:
        Success response with list of todos

    Raises:
        HTTPException: 403 if user_id doesn't match authenticated user
    """
    # Verify user_id in path matches authenticated user
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="FORBIDDEN",
                message="You can only access your own todos"
            )
        )

    # Query todos filtered by authenticated user_id
    result = await session.execute(
        select(Todo)
        .where(Todo.user_id == current_user.id)
        .order_by(Todo.created_at.desc())
    )
    todos = result.scalars().all()

    # Convert to response models
    todo_responses = [TodoResponse.model_validate(todo) for todo in todos]
    todo_data = [todo.model_dump() for todo in todo_responses]

    return success_response(
        data=todo_data,
        message="Todos retrieved successfully"
    )


@router.get("/users/{user_id}/todos/{id}", response_model=dict)
async def get_todo(
    user_id: UUID,
    id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Get a specific todo by ID.

    Args:
        user_id: User ID from URL path (must match authenticated user)
        id: Todo ID
        current_user: Authenticated user from JWT token
        session: Database session

    Returns:
        Success response with todo data

    Raises:
        HTTPException: 403 if user_id doesn't match authenticated user
        HTTPException: 404 if todo not found or doesn't belong to user
    """
    # Verify user_id in path matches authenticated user
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="FORBIDDEN",
                message="You can only access your own todos"
            )
        )

    # Query todo with ownership verification
    result = await session.execute(
        select(Todo)
        .where(Todo.id == id)
        .where(Todo.user_id == current_user.id)
    )
    todo = result.scalar_one_or_none()

    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                code="NOT_FOUND",
                message="Todo not found or you don't have permission to access it"
            )
        )

    # Convert to response model
    todo_response = TodoResponse.model_validate(todo)

    return success_response(
        data=todo_response.model_dump(),
        message="Todo retrieved successfully"
    )


@router.put("/users/{user_id}/todos/{id}", response_model=dict)
async def update_todo(
    user_id: UUID,
    id: UUID,
    todo_data: TodoUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Update a todo item (title and/or description).

    Args:
        user_id: User ID from URL path (must match authenticated user)
        id: Todo ID
        todo_data: Todo update data (title and/or description)
        current_user: Authenticated user from JWT token
        session: Database session

    Returns:
        Success response with updated todo data

    Raises:
        HTTPException: 403 if user_id doesn't match authenticated user or user doesn't own todo
        HTTPException: 404 if todo not found
    """
    # Verify user_id in path matches authenticated user
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="FORBIDDEN",
                message="You can only update your own todos"
            )
        )

    # Query todo with ownership verification
    result = await session.execute(
        select(Todo)
        .where(Todo.id == id)
        .where(Todo.user_id == current_user.id)
    )
    todo = result.scalar_one_or_none()

    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                code="NOT_FOUND",
                message="Todo not found or you don't have permission to update it"
            )
        )

    # Update fields if provided
    if todo_data.title is not None:
        todo.title = todo_data.title
    if todo_data.description is not None:
        todo.description = todo_data.description

    # Update timestamp
    todo.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(todo)

    # Convert to response model
    todo_response = TodoResponse.model_validate(todo)

    return success_response(
        data=todo_response.model_dump(),
        message="Todo updated successfully"
    )


@router.patch("/users/{user_id}/todos/{id}/complete", response_model=dict)
async def toggle_todo_completion(
    user_id: UUID,
    id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Toggle todo completion status.

    Args:
        user_id: User ID from URL path (must match authenticated user)
        id: Todo ID
        current_user: Authenticated user from JWT token
        session: Database session

    Returns:
        Success response with updated todo data

    Raises:
        HTTPException: 403 if user_id doesn't match authenticated user or user doesn't own todo
        HTTPException: 404 if todo not found
    """
    # Verify user_id in path matches authenticated user
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="FORBIDDEN",
                message="You can only update your own todos"
            )
        )

    # Query todo with ownership verification
    result = await session.execute(
        select(Todo)
        .where(Todo.id == id)
        .where(Todo.user_id == current_user.id)
    )
    todo = result.scalar_one_or_none()

    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                code="NOT_FOUND",
                message="Todo not found or you don't have permission to update it"
            )
        )

    # Toggle completion status
    todo.completed = not todo.completed
    todo.updated_at = datetime.utcnow()

    await session.commit()
    await session.refresh(todo)

    # Convert to response model
    todo_response = TodoResponse.model_validate(todo)

    return success_response(
        data=todo_response.model_dump(),
        message="Todo completion status updated"
    )


@router.delete("/users/{user_id}/todos/{id}", response_model=dict)
async def delete_todo(
    user_id: UUID,
    id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    """
    Delete a todo item.

    Args:
        user_id: User ID from URL path (must match authenticated user)
        id: Todo ID
        current_user: Authenticated user from JWT token
        session: Database session

    Returns:
        Success response confirming deletion

    Raises:
        HTTPException: 403 if user_id doesn't match authenticated user or user doesn't own todo
        HTTPException: 404 if todo not found
    """
    # Verify user_id in path matches authenticated user
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=error_response(
                code="FORBIDDEN",
                message="You can only delete your own todos"
            )
        )

    # Query todo with ownership verification
    result = await session.execute(
        select(Todo)
        .where(Todo.id == id)
        .where(Todo.user_id == current_user.id)
    )
    todo = result.scalar_one_or_none()

    if todo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_response(
                code="NOT_FOUND",
                message="Todo not found or you don't have permission to delete it"
            )
        )

    # Delete todo
    await session.delete(todo)
    await session.commit()

    return success_response(
        data=None,
        message="Todo deleted successfully"
    )

