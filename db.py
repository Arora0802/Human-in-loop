
import motor.motor_asyncio

MONGODB_URI = "mongodb://localhost:27017"
DB_NAME = "nbfc_collections"

client = motor.motor_asyncio.AsyncIOMotorClient(MONGODB_URI)
db = client[DB_NAME]


def get_collections():
    """FastAPI dependency that returns a dict of all MongoDB collections."""
    return {
        "accounts": db["loan_accounts"],
        "conversations": db["conversations"],
        "tasks": db["tasks"],
        "portfolio_kpis": db["portfolio_kpis"],
        "dept_configs": db["department_configs"],
        "rule_configs": db["rule_configs"],
        "model_configs": db["model_configs"],
    }