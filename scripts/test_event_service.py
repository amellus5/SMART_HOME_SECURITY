
from backend.app.services.event_service import save_detection_event

event_id = save_detection_event(
    event_type="UNKNOWN",
    person_name="UNKNOWN",
    similarity=0.32,
    snapshot_path=None,
    camera_id=None,
    member_id=None
)

print("Kiem tra Event ID:", event_id)
