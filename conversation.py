from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from bson import ObjectId

from db import get_collections
from db_base import PyObjectId
from enums import ConversationChannel, ConversationOutcome
from models import ConversationRecord, LoanAccount
from ai_layer import analyze_conversation, AISignalRequest

router = APIRouter(prefix="/conversations", tags=["Conversations"])


# REQUEST SCHEMA


class CreateConversationRequest(BaseModel):
    account_id: str
    channel: ConversationChannel
    raw_text: str
    agent_type: str  # "ai" or "human"
    telecaller_id: Optional[str] = None
    field_agent_id: Optional[str] = None
    outcome: Optional[ConversationOutcome] = None


# ENDPOINTS


@router.post("", response_model=ConversationRecord)
async def create_conversation(req: CreateConversationRequest, col=Depends(get_collections)):
    """
    Capture a conversation and enrich it with AI signal.
    Steps:
      1. Extract AISignal via LLM layer (keyword heuristics / plug in real LLM)
      2. Persist ConversationRecord
      3. Append outcome to account's disposition_history
    """
    # Step 1: AI Signal extraction
    ai_signal = await analyze_conversation(AISignalRequest(raw_text=req.raw_text))

    # Step 2: Persist conversation
    conv = ConversationRecord(
        account_id=req.account_id,
        channel=req.channel,
        raw_text=req.raw_text,
        agent_type=req.agent_type,
        telecaller_id=req.telecaller_id,
        field_agent_id=req.field_agent_id,
        ai_signal=ai_signal,
        outcome=req.outcome,
    )
    result = await col["conversations"].insert_one(conv.to_mongo())
    conv.id = PyObjectId(str(result.inserted_id))

    # Step 3: Update account disposition history
    acc_doc = await col["accounts"].find_one({"_id": ObjectId(req.account_id)})
    if acc_doc:
        account = LoanAccount.from_mongo(acc_doc)
        if req.outcome:
            account.disposition_history.append(req.outcome.value)
        await col["accounts"].update_one(
            {"_id": ObjectId(req.account_id)},
            {"$set": {"disposition_history": account.disposition_history}},
        )

    return conv


@router.get("/{account_id}", response_model=List[ConversationRecord])
async def list_conversations(account_id: str, col=Depends(get_collections)):
    """Return all conversations for an account, newest first."""
    cursor = col["conversations"].find({"account_id": account_id}).sort("created_at", -1)
    items = []
    async for doc in cursor:
        items.append(ConversationRecord.from_mongo(doc))
    return items