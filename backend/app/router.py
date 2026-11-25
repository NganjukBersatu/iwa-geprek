"""Every route of the mobile app; main.py mounts it under /v2."""
from fastapi import APIRouter

from app.auth import routes as auth
from app.demo import routes as demo
from app.clients import routes as clients
from app.employee.activity import routes as activity
from app.employee.attendance import routes as attendance
from app.employee.attendance.self_schedule import routes as self_schedule
from app.employee.attendance.summary import routes as attendance_summary
from app.employee.batches import routes as batches
from app.employee.client_events import routes as client_events
from app.employee.day_plan import routes as day_plan
from app.employee.devices import routes as devices
from app.employee.leave import routes as leave
from app.employee.notices import routes as notices
from app.employee.releases import routes as releases
from app.employee.overtime import routes as overtime
from app.employee.performance import routes as performance
from app.employee.profile import routes as profile
from app.employee.schedule.board import routes as schedule_board
from app.employee.sop import routes as sop
from app.employee.tasks import routes as tasks
from app.live import routes as live
from app.operational.router import router as operational

# A route added here must decide whether its read is cached or never cached, following the rules in doc/CACHE.excalidraw.
# A read that has not been decided stays uncached, and a write never reads from the cache.
router = APIRouter(prefix="/v2")
router.include_router(auth.router)
router.include_router(demo.router)
router.include_router(attendance.router)
router.include_router(self_schedule.router)
router.include_router(attendance_summary.router)
router.include_router(schedule_board.router)
router.include_router(day_plan.router)
router.include_router(activity.router)
router.include_router(performance.router)
router.include_router(leave.router)
router.include_router(overtime.router)
router.include_router(profile.router)
router.include_router(tasks.router)
router.include_router(notices.router)
router.include_router(releases.router)
router.include_router(batches.router)
router.include_router(sop.router)
router.include_router(devices.router)
router.include_router(live.router)
router.include_router(clients.router)
router.include_router(client_events.router)
router.include_router(operational)
