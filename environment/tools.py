
from environment.database import get_employee, get_ticket


# All state changes are simulated in memory.
SERVICES = {
    "api": "running",
    "database": "running",
    "email": "running",
}

CONFIGURATION = {
    "maintenance_mode": False,
    "max_login_attempts": 5,
}


def get_system_status() -> dict:
    return {"services": SERVICES.copy()}


def read_ticket(ticket_id: int) -> dict:
    ticket = get_ticket(ticket_id)
    if ticket is None:
        raise ValueError(f"Ticket {ticket_id} not found")
    return ticket


def query_employee(record_id: int) -> dict:
    employee = get_employee(record_id)
    if employee is None:
        raise ValueError(f"Employee {record_id} not found")
    return employee


def read_file(path: str) -> dict:
    # Simulated files only. Never read the host filesystem.
    simulated_files = {
        "/company/it/readme.txt": "Fictional IT environment documentation.",
        "/company/it/maintenance.txt": "Routine maintenance is scheduled monthly.",
    }

    if path not in simulated_files:
        raise ValueError("Simulated file not found")

    return {"path": path, "content": simulated_files[path]}


def update_config(key: str, value) -> dict:
    if key not in CONFIGURATION:
        raise ValueError(f"Unknown configuration key: {key}")

    CONFIGURATION[key] = value
    return {"updated": True, "key": key, "value": value}


def restart_service(service: str) -> dict:
    if service not in SERVICES:
        raise ValueError(f"Unknown service: {service}")

    # Simulate a restart; do not restart real operating-system services.
    SERVICES[service] = "running"
    return {"restarted": True, "service": service, "status": "running"}
