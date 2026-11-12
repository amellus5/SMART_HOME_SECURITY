
const API_BASE_URL = "http://127.0.0.1:8000";

// ========================================
// HIEN THI THONG KE
// ========================================

async function loadStatistics() {
    const totalElement = document.getElementById("totalEvents");
    const knownElement = document.getElementById("knownEvents");
    const unknownElement = document.getElementById("unknownEvents");

    try {
        const response = await fetch(`${API_BASE_URL}/api/events/stats`);

        if (!response.ok) {
            throw new Error("Khong the tai thong ke.");
        }

        const result = await response.json();

        totalElement.textContent =
            result.statistics.total_events;

        knownElement.textContent =
            result.statistics.known_events;

        unknownElement.textContent =
            result.statistics.unknown_events;

        renderLatestEvent(result.latest_event);

    } catch (error) {
        console.error("Loi tai thong ke:", error);

        totalElement.textContent = "--";
        knownElement.textContent = "--";
        unknownElement.textContent = "--";
    }
}


// ========================================
// HIEN THI SU KIEN MOI NHAT
// ========================================

function renderLatestEvent(event) {
    const container = document.getElementById("latestEvent");

    if (!event) {
        container.innerHTML = `
            <div class="empty-state">
                Chua co su kien nao.
            </div>
        `;
        return;
    }

    const isUnknown = event.event_type === "UNKNOWN";

    const badgeClass = isUnknown ? "unknown" : "known";

    const eventName = isUnknown
        ? "Nguoi chua nhan dien"
        : escapeHTML(event.person_name || "Thanh vien");

    const similarity = Number(event.similarity);

    const similarityText = Number.isFinite(similarity)
        ? `${(similarity * 100).toFixed(2)}%`
        : "Khong co du lieu";

    const snapshotHTML = event.snapshot_path
        ? `
            <img
                class="latest-event-image"
                src="${API_BASE_URL}/api/events/${event.id}/snapshot"
                alt="Anh su kien"
            >
        `
        : `
            <div class="latest-event-image empty-state">
                Khong co anh
            </div>
        `;

    container.innerHTML = `
        <div class="latest-event-content">

            ${snapshotHTML}

            <div class="latest-event-info">

                <h6>
                    <span class="event-badge ${badgeClass}">
                        ${event.event_type}
                    </span>
                    ${eventName}
                </h6>

                <p>
                    ID su kien: #${Number(event.id)}
                </p>

                <p>
                    Do tuong dong: ${similarityText}
                </p>

                <p>
                    Thoi gian: ${escapeHTML(event.detected_at || "")}
                </p>

            </div>

        </div>
    `;
}


// ========================================
// HIEN THI LICH SU PHAT HIEN
// ========================================

async function loadEvents() {
    const tableBody = document.getElementById("eventTableBody");

    try {
        const response = await fetch(
            `${API_BASE_URL}/api/events/?limit=50`
        );

        if (!response.ok) {
            throw new Error("Khong the tai lich su su kien.");
        }

        const result = await response.json();

        renderEvents(result.events);

    } catch (error) {
        console.error("Loi tai lich su:", error);

        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    Khong the ket noi Backend.
                </td>
            </tr>
        `;
    }
}


// ========================================
// RENDER BANG SU KIEN
// ========================================

function renderEvents(events) {
    const tableBody = document.getElementById("eventTableBody");

    if (!events || events.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="empty-state">
                    Chua co du lieu su kien.
                </td>
            </tr>
        `;
        return;
    }

    tableBody.innerHTML = events.map(event => {

        const isUnknown = event.event_type === "UNKNOWN";

        const badgeClass = isUnknown ? "unknown" : "known";

        const personName = isUnknown
            ? "Nguoi chua nhan dien"
            : escapeHTML(event.person_name || "Thanh vien");

        const similarity = Number(event.similarity);

        const similarityText = Number.isFinite(similarity)
            ? `${(similarity * 100).toFixed(2)}%`
            : "--";

        const snapshotHTML = event.snapshot_path
            ? `
                <a
                    class="snapshot-link"
                    href="${API_BASE_URL}/api/events/${Number(event.id)}/snapshot"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Xem anh
                </a>
            `
            : "Khong co anh";

        return `
            <tr>

                <td>#${Number(event.id)}</td>

                <td>
                    <span class="event-badge ${badgeClass}">
                        ${event.event_type}
                    </span>
                </td>

                <td>${personName}</td>

                <td>${similarityText}</td>

                <td>${escapeHTML(event.detected_at || "")}</td>

                <td>${snapshotHTML}</td>

            </tr>
        `;

    }).join("");
}


// ========================================
// ESCAPE DU LIEU HIEN THI
// ========================================

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, character => {
        const entities = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        };

        return entities[character];
    });
}


// ========================================
// KHOI DONG DASHBOARD
// ========================================

async function initializeDashboard() {
    await Promise.all([
        loadStatistics(),
        loadEvents()
    ]);
}

document.addEventListener("DOMContentLoaded", () => {
    initializeDashboard();

    // Cap nhat du lieu moi moi 30 giay.
    setInterval(initializeDashboard, 30000);
});
