
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from environment.database import (
    get_employee,
    get_ticket,
    initialize_database,
    list_employees,
    list_tickets,
)


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


@app.get("/")
def home():
    return {
        "message": "AI IT Administration Portal is running",
        "status": "ok",
    }


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
