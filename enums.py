from enum import Enum


class LoanType(str, Enum):
    MICRO = "micro"
    FARMER = "farmer"
    SECURED = "secured"
    UNSECURED = "unsecured"
    DIGITAL = "digital"


class RiskTag(str, Enum):
    ASSET_RISK = "asset_risk"
    FRAUD_SUSPICION = "fraud_suspicion"
    FINANCIAL_HARDSHIP = "financial_hardship"
    TEMPORARY_HARDSHIP = "temporary_hardship"
    NON_RESPONSIVE = "non_responsive"
    DISPUTE = "dispute"
    COMPLIANCE_FLAG = "compliance_flag"


class IntentCategory(str, Enum):
    WILL_PAY = "will_pay"
    CANNOT_PAY = "cannot_pay"
    DISPUTE = "dispute"
    HARDSHIP = "hardship"
    UNKNOWN = "unknown"


class RecoveryScoreBand(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Department(str, Enum):
    AI_INTELLIGENCE = "ai_data_intelligence"
    TELECALLING = "telecalling_operations"
    FIELD = "field_operations"
    RISK_CREDIT = "risk_credit_monitoring"
    COMPLIANCE = "compliance_audit"
    PRODUCT_TECH = "product_technology"
    PORTFOLIO_STRATEGY = "portfolio_strategy"
    LEGAL = "legal"


class AccountStatus(str, Enum):
    CURRENT = "current"
    DELINQUENT = "delinquent"
    WRITE_OFF_EVAL = "write_off_evaluation"
    LEGAL = "legal"
    RECOVERED = "recovered"


class ConversationChannel(str, Enum):
    VOICE = "voice"
    WHATSAPP = "whatsapp"
    SMS = "sms"
    APP = "app"


class ConversationOutcome(str, Enum):
    PROMISE_TO_PAY = "promise_to_pay"
    PART_PAYMENT = "part_payment"
    DISPUTE_RAISED = "dispute_raised"
    HARDHIP_REPORTED = "hardship_reported"
    NO_RESPONSE = "no_response"
    FULL_PAYMENT = "full_payment"
    BROKEN_PROMISE = "broken_promise"


class TaskType(str, Enum):
    TELECALL = "telecall"
    FIELD_VISIT = "field_visit"
    COMPLIANCE_REVIEW = "compliance_review"
    LEGAL_REVIEW = "legal_review"


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"