from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from db_base import MongoBaseModel, PyObjectId
from enums import (
    LoanType, RiskTag, IntentCategory, RecoveryScoreBand,
    Department, AccountStatus, ConversationChannel,
    ConversationOutcome, TaskType, TaskStatus,
)


# CUSTOMER & LOAN ACCOUNT


class Customer(BaseModel):
    customer_id: str
    name: str
    mobile: str
    address: str
    region: str


class LoanAccount(MongoBaseModel):
    nbfc_id: str
    customer: Customer
    loan_type: LoanType
    principal_amount: float
    outstanding_amount: float
    dpd: int  # days past due
    last_payment_date: Optional[datetime] = None
    status: AccountStatus = AccountStatus.DELINQUENT
    digital_engagement_score: float = 0.0  # 0–1
    call_pickup_rate: float = 0.0          # 0–1
    promise_to_pay_count: int = 0
    disposition_history: List[str] = []
    region: str
    risk_tags: List[RiskTag] = []
    recovery_probability: Optional[float] = None
    field_visit_score: Optional[float] = None
    last_routed_department: Optional[Department] = None



# AI SIGNAL & CONVERSATION


class AISignal(BaseModel):
    intent: IntentCategory
    sentiment: str  # "positive", "neutral", "negative"
    risk_tags: List[RiskTag] = []
    escalation_flag: bool = False
    suggested_resolution: Optional[str] = None
    recovery_score_band: RecoveryScoreBand = RecoveryScoreBand.MEDIUM
    recovery_probability: Optional[float] = None
    field_visit_trigger_score: Optional[float] = None


class ConversationRecord(MongoBaseModel):
    account_id: str
    channel: ConversationChannel
    raw_text: str
    agent_type: str  # "ai" or "human"
    telecaller_id: Optional[str] = None
    field_agent_id: Optional[str] = None
    ai_signal: Optional[AISignal] = None
    outcome: Optional[ConversationOutcome] = None
    next_best_action: Optional[str] = None
    assigned_department: Optional[Department] = None



# TASKS


class Task(MongoBaseModel):
    account_id: str
    task_type: TaskType
    assigned_department: Department
    assigned_to: Optional[str] = None
    status: TaskStatus = TaskStatus.PENDING
    details: Optional[str] = None
    due_date: Optional[datetime] = None
    metadata: Dict[str, Any] = {}



# PORTFOLIO KPIs


class PortfolioKPI(MongoBaseModel):
    nbfc_id: str
    loan_type: LoanType
    date: datetime
    total_accounts: int
    total_delinquent: int
    avg_dpd: float
    recovery_rate: float
    field_visit_count: int
    ai_score_effectiveness: float  # e.g. KS / AUC / uplift


# CONFIG MODELS


class DepartmentConfig(MongoBaseModel):
    name: Department
    description: str
    routing_threshold_min: float = 0.0
    routing_threshold_max: float = 1.0
    max_daily_tasks: int = 1000


class RuleConfig(MongoBaseModel):
    name: str
    description: str
    is_active: bool = True
    condition: Dict[str, Any]  # e.g. {"dpd_gt": 60}
    action: Dict[str, Any]     # e.g. {"route_to": "field"}


class ModelConfig(MongoBaseModel):
    name: str
    version: str
    type: str  # "ml_recovery", "llm_intent"
    hyperparams: Dict[str, Any] = {}
    is_active: bool = True