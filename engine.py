from typing import Dict, Any, Optional

from enums import (
    RecoveryScoreBand, Department, LoanType,
    RiskTag, ConversationOutcome,
)
from models import LoanAccount, AISignal


def apply_rule_engine(account: LoanAccount, ai_signal: Optional[AISignal]) -> Dict[str, Any]:
    """
     Rule engine (zero AI cost).
      - DPD > 60 → field candidate
      - 3 non-responses → escalation to field
      - Asset loan + asset risk tag → insurance workflow
      - Compliance flag from LLM signal → compliance task
    Returns a dict of routing actions consumed by the score-and-route endpoint.
    """
    actions: Dict[str, Any] = {
        "route_to_department": None,
        "create_field_task": False,
        "create_compliance_task": False,
        "routing_band": None,
        "routing_comment": "",
    }

    # Derive band from recovery probability
    prob = account.recovery_probability or 0.0
    if prob >= 0.8:
        band = RecoveryScoreBand.HIGH
    elif prob >= 0.5:
        band = RecoveryScoreBand.MEDIUM
    else:
        band = RecoveryScoreBand.LOW

    actions["routing_band"] = band.value

    # Routing table (Section 5 / routing logic)
    if prob >= 0.8:
        actions["route_to_department"] = Department.TELECALLING
        actions["routing_comment"] = "Telecaller priority"
    elif prob >= 0.5:
        actions["route_to_department"] = Department.TELECALLING
        actions["routing_comment"] = "Normal follow-up"
    elif prob >= 0.2:
        actions["route_to_department"] = Department.AI_INTELLIGENCE
        actions["routing_comment"] = "Automated reminder"
    else:
        actions["route_to_department"] = Department.LEGAL
        actions["routing_comment"] = "Legal / write-off evaluation"

    # DPD-based rule: >60 days past due triggers field visit
    if account.dpd > 60:
        actions["create_field_task"] = True

    # Non-response heuristic: ≥3 NO_RESPONSE dispositions → field escalation
    no_resp_count = sum(
        1 for d in account.disposition_history
        if d == ConversationOutcome.NO_RESPONSE.value
    )
    if no_resp_count >= 3:
        actions["create_field_task"] = True

    # Scenario 1: Asset loan + asset risk tag → insurance / asset verification
    if account.loan_type in [LoanType.SECURED] and ai_signal:
        if RiskTag.ASSET_RISK in ai_signal.risk_tags:
            actions["create_field_task"] = True
            actions["routing_comment"] += " | Insurance / asset verification required"

    # Compliance flag from LLM signal → compliance review task
    if ai_signal and RiskTag.COMPLIANCE_FLAG in ai_signal.risk_tags:
        actions["create_compliance_task"] = True

    return actions


def cheap_recovery_scoring(account: LoanAccount) -> Dict[str, float]:
    """
     ML-like scoring (placeholder for Logistic Regression / XGBoost).
    Inputs:  dpd, call_pickup_rate, digital_engagement_score, promise_to_pay_count.
    Outputs: recovery_probability (0–1), field_visit_score (0–1).

    Replace this function body with a call to your real trained model when ready:
        features = build_feature_vector(account)
        return your_model.predict(features)
    """
    base = 0.7

    # More DPD → lower recovery probability
    if account.dpd > 90:
        base -= 0.3
    elif account.dpd > 60:
        base -= 0.2
    elif account.dpd > 30:
        base -= 0.1

    # Call pickup and digital engagement (each contributes ±0.1)
    base += (account.call_pickup_rate - 0.5) * 0.2
    base += (account.digital_engagement_score - 0.5) * 0.2

    # Promise-to-pay history (max +0.1 bonus)
    base += min(account.promise_to_pay_count * 0.02, 0.1)

    recovery_probability = max(0.0, min(1.0, base))

    # Field visit score: high DPD + low engagement → high field visit priority
    fv = 0.0
    if account.dpd > 60:
        fv += 0.5
    if account.call_pickup_rate < 0.3:
        fv += 0.3
    if account.digital_engagement_score < 0.3:
        fv += 0.2
    field_visit_score = max(0.0, min(1.0, fv))

    return {
        "recovery_probability": recovery_probability,
        "field_visit_score": field_visit_score,
    }