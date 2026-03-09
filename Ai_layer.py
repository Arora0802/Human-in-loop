from typing import List
from fastapi import APIRouter
from pydantic import BaseModel

from enums import IntentCategory, RiskTag, RecoveryScoreBand
from models import AISignal

router = APIRouter(prefix="/ai", tags=["AI Signal"])


class AISignalRequest(BaseModel):
    raw_text: str


@router.post("/analyze", response_model=AISignal)
async def analyze_conversation(req: AISignalRequest) -> AISignal:
    """
    5 NBFC collection scenarios:
      Scenario 1 – Secured asset stolen       → ASSET_RISK, CANNOT_PAY
      Scenario 2 – Business/cash hardship      → FINANCIAL_HARDSHIP, HARDSHIP
      Scenario 3 – Loan dispute / fraud        → FRAUD_SUSPICION, DISPUTE
      Scenario 4 – Accident / temp hardship    → TEMPORARY_HARDSHIP, HARDSHIP
      Scenario 5 – Promise to pay              → WILL_PAY
    Compliance escalation is triggered by harassment / legal threat keywords.
    """
    text = req.raw_text.lower()

    intent = IntentCategory.UNKNOWN
    risk_tags: List[RiskTag] = []
    suggested_resolution = None
    escalation_flag = False

    # Scenario 1: Asset loan – vehicle / asset stolen
    if "stolen" in text:
        intent = IntentCategory.CANNOT_PAY
        risk_tags.append(RiskTag.ASSET_RISK)
        suggested_resolution = "Verify FIR and insurance claim, move to insurance workflow."

    # Scenario 2: Business / cash flow hardship
    elif "business" in text or "cash" in text:
        intent = IntentCategory.HARDSHIP
        risk_tags.append(RiskTag.FINANCIAL_HARDSHIP)
        suggested_resolution = "Offer structured part payment and reschedule."

    # Scenario 3: Loan dispute / fraud suspicion
    elif "did not take" in text or "not my loan" in text:
        intent = IntentCategory.DISPUTE
        risk_tags.append(RiskTag.FRAUD_SUSPICION)
        risk_tags.append(RiskTag.DISPUTE)
        suggested_resolution = "Move to dispute & KYC verification flow."

    # Scenario 4: Temporary hardship (accident / medical)
    elif "accident" in text:
        intent = IntentCategory.HARDSHIP
        risk_tags.append(RiskTag.TEMPORARY_HARDSHIP)
        suggested_resolution = "Confirm insurance claim and monitor payout timeline."

    # Scenario 5: Promise to pay
    elif "will pay" in text or "i will pay" in text:
        intent = IntentCategory.WILL_PAY

    # Sentiment + compliance escalation detection
    if any(x in text for x in ["angry", "harass", "complain", "police"]):
        sentiment = "negative"
        risk_tags.append(RiskTag.COMPLIANCE_FLAG)
        escalation_flag = True
    elif any(x in text for x in ["thank", "ok", "fine"]):
        sentiment = "positive"
    else:
        sentiment = "neutral"

    return AISignal(
        intent=intent,
        sentiment=sentiment,
        risk_tags=list(set(risk_tags)),
        escalation_flag=escalation_flag,
        suggested_resolution=suggested_resolution,
        recovery_score_band=RecoveryScoreBand.MEDIUM,
        recovery_probability=None,
        field_visit_trigger_score=None,
    )