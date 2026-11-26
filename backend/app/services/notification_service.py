
import os
import requests
from dotenv import load_dotenv

# Nap cau hinh tu file .env
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
ENV_PATH = os.path.join(PROJECT_ROOT, ".env")

load_dotenv(ENV_PATH)

NTFY_SERVER = os.getenv("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
NTFY_TOPIC = os.getenv("NTFY_TOPIC")


def send_unknown_notification(event_id, detected_at=None):
    """
    Gui thong bao khi he thong phat hien khuon mat UNKNOWN.
    """

    if not NTFY_TOPIC:
        print("LOI: Chua cau hinh NTFY_TOPIC!")
        return False

    title = "CANH BAO - SMART HOME SECURITY"

    message = (
        f"Phat hien khuon mat la!\n"
        f"Ma su kien: #{event_id}\n"
        f"Thoi gian: {detected_at or 'Khong xac dinh'}"
    )

    url = f"{NTFY_SERVER}/{NTFY_TOPIC}"

    headers = {
        "Title": title,
        "Priority": "urgent",
        "Tags": "warning,house"
    }

    try:
        response = requests.post(
            url,
            data=message.encode("utf-8"),
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        print("DA GUI CANH BAO DEN DIEN THOAI!")
        print("Event ID:", event_id)

        return True

    except requests.RequestException as error:
        print("LOI GUI THONG BAO NTFY:", error)
        return False
