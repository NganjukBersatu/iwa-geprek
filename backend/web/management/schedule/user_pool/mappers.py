"""Turns people into the schedule pool's response schema."""
from app.models.user import User
from web.management.schedule.user_pool.schemas import PoolUserOut


def pool_user_out(user: User) -> PoolUserOut:
    return PoolUserOut(id=user.id, outlet_id=user.outlet_id, username=user.username, name=user.name, role_name=user.role.name if user.role else "-")
