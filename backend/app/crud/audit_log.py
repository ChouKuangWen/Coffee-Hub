"""Compatibility entry: same transaction, no swallowed audit failures."""
from app.services.audit_log_service import record_required_action


async def create_audit_log(db, obj_in):
    from types import SimpleNamespace
    data = obj_in.model_dump()
    request = SimpleNamespace(state=SimpleNamespace(request_id=data.get("request_id")))
    await record_required_action(db, request, user_id=data.get("user_id"), category=data["category"],
        action=data["action"], target_type=data.get("target_type"), target_id=data.get("target_id"),
        status=data.get("status", "SUCCESS"), before_data=data.get("before_data"), after_data=data.get("after_data"))
