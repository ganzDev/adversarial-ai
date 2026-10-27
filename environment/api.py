
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from environment.database import (
    get_employee,
    get_ticket,
    initialize_database,
    list_employees,
    list_tickets,
)

from pydantic import BaseModel, Field
from fastapi import Query

from agents.decision import VictimDecisionLayer
from environment.audit_log import (
    initialize_audit_log,
    list_tool_events,
    clear_tool_events,
    delete_tool_event,
)

from pathlib import Path
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="AI IT Administration Portal",
    description="A simulated environment for testing AI agent security.",
    version="0.2.0",
    lifespan=lifespan,
)

BASE_DIR = Path(__file__).resolve().parent

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)


@app.get("/")
def root():
    return FileResponse(BASE_DIR / "templates" / "dashboard.html")

@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.get("/employees")
def employees():
    return {"employees": list_employees()}


@app.get("/employees/{employee_id}")
def employee_details(employee_id: int):
    employee = get_employee(employee_id)
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@app.get("/tickets")
def tickets():
    return {"tickets": list_tickets()}


@app.get("/tickets/{ticket_id}")
def ticket_details(ticket_id: int):
    ticket = get_ticket(ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


class InstructionRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=4000)


@app.post("/assistant/instruction")
def submit_instruction(request: InstructionRequest):
    """Submit an instruction to the victim AI."""
    instruction = request.instruction.strip()

    if not instruction:
        return {
            "message": "Please provide an instruction.",
            "proposed_tool": None,
            "tool_result": None,
        }

    decision_layer = VictimDecisionLayer()
    return decision_layer.handle_instruction(instruction)


@app.get("/audit-events")
def get_audit_events(
    limit: int = Query(default=50, ge=1, le=500),
):
    """Return recent security audit events."""
    initialize_audit_log()
    return {"events": list_tool_events(limit=limit)}

@app.delete("/audit-events")
def delete_audit_events():
    """Clear local audit history after explicit confirmation in the UI."""
    initialize_audit_log()
    deleted_count = clear_tool_events()
    return {
        "message": "Audit history cleared.",
        "deleted_count": deleted_count,
    }



@app.delete("/audit-events/{event_id}")
def delete_single_audit_event(event_id: str):
    """Delete one audit event by its unique ID."""
    initialize_audit_log()
    deleted = delete_tool_event(event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Audit event not found")
    return {
        "message": "Audit event deleted.",
        "event_id": event_id,
    }
