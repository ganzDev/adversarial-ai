const instructionForm = document.getElementById("instruction-form");
const instructionInput = document.getElementById("instruction");
const submitButton = document.getElementById("submit-button");
const refreshButton = document.getElementById("refresh-button");
const eventLimit = document.getElementById("event-limit");

const assistantStatus = document.getElementById("assistant-status");
const assistantResult = document.getElementById("assistant-result");
const auditStatus = document.getElementById("audit-status");
const auditTableBody = document.getElementById("audit-table-body");

// Keep a direct reference to the panel. It remains available even when
// its table row is temporarily detached from the document.
const eventDetailsPanel = document.getElementById("event-details");

let allEvents = [];
let selectedEventId = null;

function setNotice(element, message, type = "") {
    if (!element) return;
    element.textContent = message;
    element.className = `notice ${type}`.trim();
}

function setText(id, value) {
    const element = document.getElementById(id);
    if (!element) return;

    element.textContent =
        value === null || value === undefined || value === ""
            ? "—"
            : String(value);
}

function formatDate(timestamp) {
    if (!timestamp) return "—";

    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return String(timestamp);

    return date.toLocaleString(undefined, {
        timeZone: "UTC",
        dateStyle: "medium",
        timeStyle: "medium",
    }) + " UTC";
}

function makePill(value, fallback = "Unknown") {
    const pill = document.createElement("span");
    const label = value || fallback;

    pill.className = `pill ${String(label).toLowerCase()}`;
    pill.textContent = label;

    return pill;
}

function addCell(row, value) {
    const cell = document.createElement("td");

    cell.textContent =
        value === null || value === undefined || value === ""
            ? "—"
            : String(value);

    row.appendChild(cell);
    return cell;
}

function getDecision(event) {
    return event.outcome ||
        (event.allowed ? "authorized" : "denied");
}

function closeEventDetails() {
    const detailsRow = document.getElementById("event-details-row");

    if (eventDetailsPanel) {
        eventDetailsPanel.classList.add("hidden");
    }

    // Hide instead of removing the row. This keeps the panel in the DOM.
    if (detailsRow) {
        detailsRow.classList.add("hidden");
    }

    selectedEventId = null;

    document.querySelectorAll("#audit-table-body tr").forEach(row => {
        row.classList.remove("selected-event");
    });
}

function showEventDetails(event, selectedRow) {
    if (!eventDetailsPanel || !selectedRow) {
        console.error("Cannot open event details: the panel or selected row is missing.");
        return;
    }

    const fields = {
        "detail-event-id": event.event_id,
        "detail-timestamp": formatDate(event.timestamp),
        "detail-tool": event.tool,
        "detail-resource": event.resource,
        "detail-operation": event.operation,
        "detail-reason": event.reason || "No reason recorded.",
    };

    for (const [id, value] of Object.entries(fields)) {
        setText(id, value);
    }

    const authorization = document.getElementById("detail-authorization");
    if (authorization) {
        authorization.replaceChildren(
            makePill(
                event.allowed ? "Allowed" : "Denied",
                getDecision(event)
            )
        );
    }

    const risk = document.getElementById("detail-risk");
    if (risk) {
        risk.replaceChildren(makePill(event.risk));
    }

    const outcome = document.getElementById("detail-outcome");
    if (outcome) {
        outcome.replaceChildren(makePill(event.outcome || "Unknown"));
    }

    setText(
        "detail-event-subtitle",
        `${event.tool || "Unknown tool"} · ${event.operation || "Unknown operation"}`
    );

    const argumentsElement = document.getElementById("detail-arguments");
    if (argumentsElement) {
        argumentsElement.textContent =
            JSON.stringify(event.arguments ?? {}, null, 2);
    }

    // Reuse the same panel and details row every time.
    let detailsRow = document.getElementById("event-details-row");

    if (!detailsRow) {
        detailsRow = document.createElement("tr");
        detailsRow.id = "event-details-row";

        const detailsCell = document.createElement("td");
        detailsCell.colSpan = 7;
        detailsCell.style.padding = "0";

        // Use the cached reference, not getElementById(), because the
        // panel may currently be detached from the document.
        detailsCell.appendChild(eventDetailsPanel);
        detailsRow.appendChild(detailsCell);
    }

    // Move the row below the selected event, then reveal it.
    selectedRow.insertAdjacentElement("afterend", detailsRow);

    detailsRow.classList.remove("hidden");
    eventDetailsPanel.classList.remove("hidden");
    selectedEventId = event.event_id;

    document.querySelectorAll("#audit-table-body tr").forEach(row => {
        row.classList.remove("selected-event");
    });

    selectedRow.classList.add("selected-event");
}

function renderAuditEvents() {
    const decisionFilter = document.getElementById("decision-filter");
    const riskFilter = document.getElementById("risk-filter");
    const timeFilter = document.getElementById("time-filter");
    const limitSelect = document.getElementById("event-limit");

    if (!auditTableBody || !decisionFilter || !riskFilter ||
        !timeFilter || !limitSelect) {
        console.error("One or more audit table or filter elements are missing.");
        return;
    }

    const decision = decisionFilter.value;
    const risk = riskFilter.value;
    const timeRange = timeFilter.value;
    const displayLimit = Number(limitSelect.value) || 50;

    const now = Date.now();
    const cutoff = timeRange === "all"
        ? null
        : now - Number(timeRange) * 60 * 60 * 1000;

    const filtered = allEvents.filter(event => {
        if (decision !== "all" && getDecision(event) !== decision) {
            return false;
        }

        if (risk !== "all" && event.risk !== risk) {
            return false;
        }

        if (cutoff !== null) {
            const timestamp = new Date(event.timestamp).getTime();

            if (!Number.isFinite(timestamp) ||
                timestamp < cutoff ||
                timestamp > now) {
                return false;
            }
        }

        return true;
    });

    setText("total-events", filtered.length);
    setText(
        "denied-events",
        filtered.filter(event => getDecision(event) === "denied").length
    );
    setText(
        "rejected-events",
        filtered.filter(event => getDecision(event) === "rejected").length
    );
    setText(
        "high-risk-events",
        filtered.filter(event => event.risk === "high").length
    );

    // Clear table rows without losing our cached reference to the panel.
    auditTableBody.replaceChildren();

    const visibleEvents = filtered.slice(0, displayLimit);
    let selectedRowForDetails = null;

    if (visibleEvents.length === 0) {
        const row = document.createElement("tr");
        const cell = addCell(row, "No events match these filters.");
        cell.colSpan = 7;
        auditTableBody.appendChild(row);
    } else {
        for (const event of visibleEvents) {
            const row = document.createElement("tr");

            addCell(row, formatDate(event.timestamp));
            addCell(row, event.tool);
            addCell(row, event.operation);

            const riskCell = document.createElement("td");
            riskCell.appendChild(makePill(event.risk));
            row.appendChild(riskCell);

            const decisionCell = document.createElement("td");
            decisionCell.appendChild(makePill(getDecision(event)));
            row.appendChild(decisionCell);

            addCell(row, event.reason);

            const detailsCell = document.createElement("td");
            const detailsButton = document.createElement("button");

            detailsButton.type = "button";
            detailsButton.className = "details-button";
            detailsButton.textContent = "Inspect";

            detailsButton.addEventListener("click", () => {
                showEventDetails(event, row);
            });

            detailsCell.appendChild(detailsButton);

            const deleteButton = document.createElement("button");
            deleteButton.type = "button";
            deleteButton.className = "details-button delete-event-button";
            deleteButton.textContent = "Delete";
            deleteButton.setAttribute(
                "aria-label",
                `Delete audit event from ${formatDate(event.timestamp)}`
            );
            deleteButton.addEventListener("click", async () => {
                const confirmed = window.confirm(
                    `Delete this audit event for "${event.tool}"? ` +
                    "This cannot be undone."
                );

                if (!confirmed) return;

                deleteButton.disabled = true;
                detailsButton.disabled = true;

                try {
                    const response = await fetch(
                        `/audit-events/${encodeURIComponent(event.event_id)}`,
                        { method: "DELETE" }
                    );
                    const data = await response.json();

                    if (!response.ok) {
                        throw new Error(
                            data.detail || "Could not delete this audit event."
                        );
                    }

                    if (selectedEventId === event.event_id) {
                        closeEventDetails();
                    }

                    setNotice(auditStatus, "Audit event deleted.", "success");
                    await fetchAuditEvents();
                } catch (error) {
                    setNotice(auditStatus, error.message, "error");
                    deleteButton.disabled = false;
                    detailsButton.disabled = false;
                }
            });

            detailsCell.appendChild(deleteButton);
            row.appendChild(detailsCell);
            auditTableBody.appendChild(row);

            if (selectedEventId === event.event_id) {
                selectedRowForDetails = row;
            }
        }
    }

    // Restore the expanded panel after a refresh if its event is still visible.
    if (selectedRowForDetails) {
        showEventDetails(
            visibleEvents.find(event => event.event_id === selectedEventId),
            selectedRowForDetails
        );
    } else {
        closeEventDetails();
    }

    const suffix = filtered.length > displayLimit
        ? ` Showing the first ${displayLimit}.`
        : "";

    setNotice(
        auditStatus,
        `${filtered.length} event(s) match the filters.${suffix}`,
        "success"
    );
}

async function fetchAuditEvents() {
    setNotice(auditStatus, "Loading audit events...");

    try {
        const response = await fetch("/audit-events?limit=500");

        if (!response.ok) {
            throw new Error(`Audit API returned HTTP ${response.status}`);
        }

        const data = await response.json();
        allEvents = Array.isArray(data.events) ? data.events : [];

        renderAuditEvents();
    } catch (error) {
        setNotice(
            auditStatus,
            `Could not load audit events: ${error.message}`,
            "error"
        );
    }
}

function displayAssistantResult(data) {
    if (!assistantResult) return;

    assistantResult.classList.remove("hidden");

    setText("assistant-message", data.message);
    setText("proposed-tool", data.proposed_tool);

    const toolResult = data.tool_result;
    const authorization = document.getElementById("authorization-result");
    const risk = document.getElementById("risk-result");
    const resultJson = document.getElementById("tool-result-json");

    if (authorization) authorization.className = "pill neutral";
    if (risk) risk.className = "pill neutral";

    if (toolResult && typeof toolResult === "object") {
        const decision = toolResult.allowed ? "Allowed" : "Denied";

        if (authorization) {
            authorization.textContent = decision;
            authorization.className =
                `pill ${toolResult.allowed ? "allowed" : "denied"}`;
        }

        if (risk) {
            risk.textContent = toolResult.risk || "Unknown";
            risk.className =
                `pill ${String(toolResult.risk || "neutral").toLowerCase()}`;
        }

        if (resultJson) {
            resultJson.textContent = JSON.stringify(toolResult, null, 2);
        }
    } else {
        if (authorization) authorization.textContent = "No tool result";
        if (risk) risk.textContent = "Not applicable";

        if (resultJson) {
            resultJson.textContent =
                "The assistant did not return a tool result.";
        }
    }
}

if (instructionForm) {
    instructionForm.addEventListener("submit", async event => {
        event.preventDefault();

        const instruction = instructionInput?.value.trim();

        if (!instruction) {
            setNotice(assistantStatus, "Enter an instruction first.", "error");
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = "Processing...";
        setNotice(assistantStatus, "Sending instruction to the victim AI...");

        try {
            const response = await fetch("/assistant/instruction", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ instruction }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || `API returned HTTP ${response.status}`
                );
            }

            displayAssistantResult(data);

            const denied =
                data.tool_result && data.tool_result.allowed === false;

            setNotice(
                assistantStatus,
                denied
                    ? "The tool action was denied. See the result and audit log below."
                    : "Instruction processed. Review the response and audit log.",
                denied ? "error" : "success"
            );

            await fetchAuditEvents();
        } catch (error) {
            setNotice(
                assistantStatus,
                `Request failed: ${error.message}`,
                "error"
            );
        } finally {
            submitButton.disabled = false;
            submitButton.textContent = "Submit instruction";
        }
    });
}

refreshButton?.addEventListener("click", fetchAuditEvents);

document.getElementById("decision-filter")
    ?.addEventListener("change", renderAuditEvents);

document.getElementById("risk-filter")
    ?.addEventListener("change", renderAuditEvents);

document.getElementById("time-filter")
    ?.addEventListener("change", renderAuditEvents);

eventLimit?.addEventListener("change", renderAuditEvents);

document.getElementById("clear-history-button")
    ?.addEventListener("click", async () => {
        const confirmed = window.confirm(
            "Delete ALL stored audit events from this local database? " +
            "This cannot be undone. Employees, tickets, and simulated " +
            "system state will not be changed."
        );

        if (!confirmed) return;

        const button = document.getElementById("clear-history-button");
        button.disabled = true;

        try {
            const response = await fetch("/audit-events", {
                method: "DELETE",
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Could not clear audit history."
                );
            }

            closeEventDetails();

            setNotice(
                auditStatus,
                `Audit history cleared. ${data.deleted_count} event(s) deleted.`,
                "success"
            );

            await fetchAuditEvents();
        } catch (error) {
            setNotice(auditStatus, error.message, "error");
        } finally {
            button.disabled = false;
        }
    });

document.getElementById("close-details")
    ?.addEventListener("click", closeEventDetails);

fetchAuditEvents();