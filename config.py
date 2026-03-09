from typing import List

from fastapi import APIRouter, Depends

from db import get_collections
from db_base import PyObjectId
from models import PortfolioKPI, DepartmentConfig, RuleConfig, ModelConfig

router = APIRouter(tags=["Portfolio & Config"])


# PORTFOLIO KPIs


@router.post("/portfolio/kpis", response_model=PortfolioKPI)
async def create_portfolio_kpi(payload: PortfolioKPI, col=Depends(get_collections)):
    """Record a new portfolio KPI snapshot for an NBFC."""
    result = await col["portfolio_kpis"].insert_one(payload.to_mongo())
    payload.id = PyObjectId(str(result.inserted_id))
    return payload


@router.get("/portfolio/kpis/{nbfc_id}", response_model=List[PortfolioKPI])
async def list_portfolio_kpis(nbfc_id: str, col=Depends(get_collections)):
    """List all KPI snapshots for a given NBFC, newest first."""
    cursor = col["portfolio_kpis"].find({"nbfc_id": nbfc_id}).sort("date", -1)
    items: List[PortfolioKPI] = []
    async for doc in cursor:
        items.append(PortfolioKPI.from_mongo(doc))
    return items


# DEPARTMENT CONFIG


@router.post("/config/departments", response_model=DepartmentConfig)
async def create_department_config(cfg: DepartmentConfig, col=Depends(get_collections)):
    """Create or update a department routing configuration."""
    result = await col["dept_configs"].insert_one(cfg.to_mongo())
    cfg.id = PyObjectId(str(result.inserted_id))
    return cfg


@router.get("/config/departments", response_model=List[DepartmentConfig])
async def list_department_configs(col=Depends(get_collections)):
    """List all department routing configurations."""
    cursor = col["dept_configs"].find({})
    items: List[DepartmentConfig] = []
    async for doc in cursor:
        items.append(DepartmentConfig.from_mongo(doc))
    return items


# RULE CONFIG


@router.post("/config/rules", response_model=RuleConfig)
async def create_rule_config(cfg: RuleConfig, col=Depends(get_collections)):
    """Register a new rule configuration (condition + action dict)."""
    result = await col["rule_configs"].insert_one(cfg.to_mongo())
    cfg.id = PyObjectId(str(result.inserted_id))
    return cfg


@router.get("/config/rules", response_model=List[RuleConfig])
async def list_rule_configs(col=Depends(get_collections)):
    """List all active and inactive rule configurations."""
    cursor = col["rule_configs"].find({})
    items: List[RuleConfig] = []
    async for doc in cursor:
        items.append(RuleConfig.from_mongo(doc))
    return items


# MODEL CONFIG

@router.post("/config/models", response_model=ModelConfig)
async def create_model_config(cfg: ModelConfig, col=Depends(get_collections)):
    """Register a new ML / LLM model configuration."""
    result = await col["model_configs"].insert_one(cfg.to_mongo())
    cfg.id = PyObjectId(str(result.inserted_id))
    return cfg


@router.get("/config/models", response_model=List[ModelConfig])
async def list_model_configs(col=Depends(get_collections)):
    """List all registered model configurations."""
    cursor = col["model_configs"].find({})
    items: List[ModelConfig] = []
    async for doc in cursor:
        items.append(ModelConfig.from_mongo(doc))
    return items