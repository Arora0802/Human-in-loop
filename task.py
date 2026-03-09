
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from datetime import datetime

from db import get_collections
from enums import Department, TaskStatus
from models import Task

router = APIRouter(prefix="/tasks", tags=["Tasks"])



# REQUEST SCHEMA


class UpdateTaskStatusRequest(BaseModel):
    status: TaskStatus



# ENDPOINTS


@router.get("", response_model=List[Task])
async def list_tasks(
    department: Optional[Department] = None,
    status: Optional[TaskStatus] = None,
    col=Depends(get_collections),
):
    """
      - department: filter by assigned department (e.g. field_operations)
      - status:     filter by task status (e.g. pending)
    """
    query: Dict[str, Any] = {}
    if department:
        query["assigned_department"] = department.value
    if status:
        query["status"] = status.value

    cursor = col["tasks"].find(query).sort("created_at", -1)
    items: List[Task] = []
    async for doc in cursor:
        items.append(Task.from_mongo(doc))
    return items


@router.patch("/{task_id}/status", response_model=Task)
async def update_task_status(
    task_id: str,
    req: UpdateTaskStatusRequest,
    col=Depends(get_collections),
):
    """Update the status of a task (e.g. field agent marks a visit completed)."""
    doc = await col["tasks"].find_one({"_id": ObjectId(task_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Task not found")

    await col["tasks"].update_one(
        {"_id": ObjectId(task_id)},
        {"$set": {"status": req.status.value, "updated_at": datetime.utcnow()}},
    )
    new_doc = await col["tasks"].find_one({"_id": ObjectId(task_id)})
    return Task.from_mongo(new_doc)