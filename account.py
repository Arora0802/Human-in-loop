from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId

from db import get_collections
from db_base import PyObjectId
from enums import (
    LoanType, AccountStatus, Department,
    TaskType,
)
from models import (
    LoanAccount, Customer, AISignal, Task,
)
from engine import cheap_recovery_scoring, apply_rule_engine

router = APIRouter(prefix="/accounts", tags=["Accounts"])


# REQUEST / RESPONSE SCHEMAS


class CreateAccountRequest(BaseModel):
    nbfc_id: str
    customer: Customer
    loan_type: LoanType
    principal_amount: float
    outstanding_amount: float
    dpd: int
    last_payment_date: Optional[datetime] = None
    status: AccountStatus = AccountStatus.DELINQUENT
    digital_engagement_score: float = 0.0
    call_pickup_rate: float = 0.0
    promise_to_pay_count: int = 0
    disposition_history: List[str] = []
    region: str


class ScoreAndRouteResponse(BaseModel):
    account: LoanAccount
    rule_actions: Dict[str, Any]
    created_tasks: List[Task]



# ENDPOINTS


@router.post("", response_model=LoanAccount)
async def create_account(payload: CreateAccountRequest, col=Depends(get_collections)):
    """Create a new delinquent loan account."""
    account = LoanAccount(
        nbfc_id=payload.nbfc_id,
        customer=payload.customer,
        loan_type=payload.loan_type,
        principal_amount=payload.principal_amount,
        outstanding_amount=payload.outstanding_amount,
        dpd=payload.dpd,
        last_payment_date=payload.last_payment_date,
        status=payload.status,
        digital_engagement_score=payload.digital_engagement_score,
        call_pickup_rate=payload.call_pickup_rate,
        promise_to_pay_count=payload.promise_to_pay_count,
        disposition_history=payload.disposition_history,
        region=payload.region,
    )
    result = await col["accounts"].insert_one(account.to_mongo())
    account.id = PyObjectId(str(result.inserted_id))
    return account


@router.get("/{account_id}", response_model=LoanAccount)
async def get_account(account_id: str, col=Depends(get_collections)):
    """Fetch a single loan account by its MongoDB ObjectId."""
    doc = await col["accounts"].find_one({"_id": ObjectId(account_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")
    return LoanAccount.from_mongo(doc)


@router.post("/{account_id}/score-and-route", response_model=ScoreAndRouteResponse)
async def score_and_route(
    account_id: str,
    ai_signal: Optional[AISignal] = None,
    col=Depends(get_collections),
):
    """
      1. ML scoring  → recovery_probability, field_visit_score
      2. Rule engine       → routing band, department, task flags
      3. Persist updates   → MongoDB
      4. Create tasks      → field visit and/or compliance review tasks
    """
    doc = await col["accounts"].find_one({"_id": ObjectId(account_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Account not found")

    account = LoanAccount.from_mongo(doc)

    # Step 1: Cheap ML scoring
    scores = cheap_recovery_scoring(account)
    account.recovery_probability = scores["recovery_probability"]
    account.field_visit_score = scores["field_visit_score"]

    # Step 2: Rule engine
    actions = apply_rule_engine(account, ai_signal)

    # Step 3: Persist routed department + scores
    if actions["route_to_department"]:
        account.last_routed_department = actions["route_to_department"]

    await col["accounts"].update_one(
        {"_id": ObjectId(account_id)},
        {"$set": account.to_mongo()},
    )

    # Step 4: Create tasks
    created_tasks: List[Task] = []

    if actions.get("create_field_task"):
        task = Task(
            account_id=account_id,
            task_type=TaskType.FIELD_VISIT,
            assigned_department=Department.FIELD,
            details="Field visit triggered by rules/score.",
            metadata={
                "dpd": account.dpd,
                "outstanding_amount": account.outstanding_amount,
                "address": account.customer.address,
                "region": account.region,
            },
        )
        result = await col["tasks"].insert_one(task.to_mongo())
        task.id = PyObjectId(str(result.inserted_id))
        created_tasks.append(task)

    if actions.get("create_compliance_task"):
        task = Task(
            account_id=account_id,
            task_type=TaskType.COMPLIANCE_REVIEW,
            assigned_department=Department.COMPLIANCE,
            details="Compliance flag from conversation.",
        )
        result = await col["tasks"].insert_one(task.to_mongo())
        task.id = PyObjectId(str(result.inserted_id))
        created_tasks.append(task)

    return ScoreAndRouteResponse(
        account=account,
        rule_actions=actions,
        created_tasks=created_tasks,
    )