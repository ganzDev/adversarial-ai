# Adversarial AI: Autonomous Exploitation and Defense of Tool-Enabled AI Agents

A capstone project for evaluating security risks in tool-enabled AI
agents inside a controlled, simulated IT administration environment.

## Project Overview

The project studies how an AI agent responds to normal instructions and
adversarial inputs when it can request actions through predefined tools.
A victim AI proposes tool calls, a security gateway is responsible for
authorizing or denying them, and an audit system records decisions and
outcomes for analysis.

The planned attack scenarios include:

-   Direct prompt injection
-   Indirect prompt injection embedded in retrieved ticket or file
    content
-   Tool abuse, including attempts to call unregistered tools
-   Privilege abuse, including unauthorized state-changing actions

The project aims to evaluate attack success rate, detection rate,
false-positive rate, and latency.

**Important implementation status:** The simulated environment, FastAPI
application, victim-agent workflow, audit logging, dashboard, and Docker
development setup are in place. The security gateway is currently a
fail-closed stub awaiting the full policy implementation. The
adversarial scenario runner and end-to-end evaluation workflow remain
integration work; do not interpret the planned scenarios or metrics as
fully implemented until verified in the current branch.

## Safety and Scope

All experiments must remain within the simulated application:

-   Use fictional employees, tickets, and organization data.
-   Read only predefined simulated file paths.
-   Apply configuration changes and service restarts only to simulated
    state.
-   Do not execute model-generated shell commands, arbitrary Python,
    host filesystem operations, or real service controls.
-   Do not use production systems, real user data, or real credentials
    in attack scenarios.
-   Treat model output and retrieved content as untrusted input, not as
    authorization.

## Architecture

``` text
Browser dashboard
       |
       v
FastAPI application (environment/api.py)
       |
       v
Victim decision layer (agents/decision.py)
       |
       v
Victim agent (agents/victim.py)
       |
       v
Security gateway (security/gateway.py)
       |
       v
Simulated tools (environment/tools.py)

SQLite stores fictional application data and security audit events.
The dashboard displays audit events and supports filtering, clearing,
and deleting individual events.
```

The gateway is the authorization boundary: model-generated tool requests
must not execute unless deterministic application code validates and
authorizes them.

## Main Components

  ----------------------------------------------------------------------------
  Path                                     Purpose
  ---------------------------------------- -----------------------------------
  `environment/api.py`                     FastAPI application, API endpoints,
                                           and instruction submission

  `environment/database.py`                SQLite database setup and fictional
                                           employees/tickets

  `environment/tool_schemas.py`            Shared `ToolRequest`, `ToolResult`,
                                           and registered tool definitions

  `environment/tools.py`                   Simulated tool implementations

  `environment/audit_log.py`               Audit-event persistence, retrieval,
                                           sanitization, clearing, and
                                           individual deletion

  `agents/decision.py`                     Model-backed decision loop and
                                           tool-request orchestration

  `agents/victim.py`                       Victim-agent tool validation and
                                           gateway routing

  `security/gateway.py`                    Gateway interface; full
                                           authorization policy is pending

  `environment/templates/dashboard.html`   Dashboard HTML

  `environment/static/dashboard.js`        Dashboard interactions and
                                           audit-event controls

  `environment/static/dashboard.css`       Dashboard styling

  `tests/`                                 Automated regression tests

  `Dockerfile`                             Container image definition

  `compose.yaml`                           Base Docker Compose service and
                                           persistent database volume

  `compose.override.yaml`                  Local development bind mounts and
                                           Uvicorn live reload
  ----------------------------------------------------------------------------

## Prerequisites

-   Git
-   Docker Desktop
-   If using Ubuntu under WSL: Docker Desktop WSL integration enabled
    for that distribution
-   An OpenAI API key for model-backed functionality

## Quick Start with Docker

Clone the repository and enter the project directory:

``` bash
git clone <repository-url>
cd adversarial-ai
```

Create a local environment file from the template:

``` bash
cp .env.example .env
```

Edit `.env` and supply your own API key. Verify that the variable names
in `.env.example` match those read by the current application code.
Never commit `.env` or share your API key.

Build and start the application:

``` bash
docker compose up -d --build
```

Check the container and API:

``` bash
docker compose ps
curl -i http://localhost:8000/health
```

A successful health request should return `HTTP 200 OK`.

Open these URLs:

-   Dashboard: <http://localhost:8000/>
-   Health endpoint: <http://localhost:8000/health>
-   Interactive API documentation: <http://localhost:8000/docs>
-   Audit events API: <http://localhost:8000/audit-events>

## Docker Development Workflow

Docker Compose combines `compose.yaml` with `compose.override.yaml`
automatically during local development. The override mounts selected
source files and directories into the container and enables Uvicorn
`--reload`.

-   Python, HTML, CSS, and JavaScript edits should normally reload
    without rebuilding the image.
-   Changes to `requirements.txt` or `Dockerfile` require rebuilding the
    image.
-   After changing Compose configuration, recreate/update the service
    with `docker compose up -d` as appropriate.

Useful commands:

``` bash
# Start in the background
docker compose up -d

# Inspect container status
docker compose ps

# Follow logs (Ctrl+C stops log viewing, not the app)
docker compose logs -f app

# Restart the app
docker compose restart app

# Stop containers while preserving the named database volume
docker compose stop

# Start again
docker compose up -d

# Rebuild after dependency or Dockerfile changes
docker compose up -d --build
```

`Up` means the container is running; it does not by itself guarantee the
API is healthy. Check `/health` and review logs when diagnosing
problems.

### Database persistence

The container stores its SQLite database at `/data/portal.db` in the
named Docker volume `portal_data`. The volume survives normal container
restarts and container recreation. The local development database at
`environment/portal.db` is separate and should remain untracked. Each
teammate will have their own database volume and audit history.

**Do not use `docker compose down -v` during routine development.** The
`-v` option removes named volumes and can delete the persistent Docker
database.

## Local Python Testing

The project has been developed with Python 3.12. If you use the existing
`uv`-managed virtual environment, activate it with:

``` bash
source .venv/bin/activate
```

Run tests with:

``` bash
pytest -q
```

When adding a dependency, install it into the project interpreter and
update `requirements.txt`. For the current `uv` workflow:

``` bash
uv pip install --python .venv/bin/python <package>
uv pip freeze --python .venv/bin/python > requirements.txt
```

Review the resulting dependency list before committing.

## Team Responsibilities

### Person 1 --- Environment and integration

-   Maintain the simulated IT environment and tool implementations.
-   Maintain the victim-agent workflow and shared request/result
    schemas.
-   Maintain FastAPI routes, audit logging, dashboard, and Docker
    development workflow.
-   Coordinate integration and regression testing.

### Person 2 --- Security gateway

-   Implement canonical tool, resource, operation, and argument
    validation in `security/gateway.py`.
-   Define authorization and risk policies, including approval
    requirements where appropriate.
-   Dispatch only to explicitly registered simulated tool functions.
-   Ensure denied requests do not change simulated state.
-   Add tests for allowed, denied, malformed, and mismatched requests.

### Person 3 --- Adversarial AI and scenarios

-   Implement a controlled scenario runner and attack inputs.
-   Cover direct and indirect prompt injection, tool abuse, and
    privilege abuse.
-   Include benign control scenarios to measure false positives.
-   Ensure attack inputs cannot bypass the victim agent or security
    gateway.
-   Record reproducible scenario/run metadata and observed outcomes.

### Shared integration contract

The victim-agent workflow uses the `ToolRequest` and `ToolResult`
definitions in `environment/tool_schemas.py`. The gateway entry point is
intended to remain:

``` python
def authorize_and_execute(request: ToolRequest) -> ToolResult:
    ...
```

Coordinate any shared signature or schema changes before merging. Verify
exact field names and function signatures in the latest checkout.

## Evaluation Metrics

Agree on metric definitions before running experiments. Suggested
starting points:

-   **Attack success rate:** successful unauthorized simulated outcomes
    divided by attack trials. Judge success by observed effects, not by
    the model claiming success.
-   **Detection rate:** attack trials correctly detected or blocked
    divided by attack trials. Document whether blocking alone counts as
    detection.
-   **False-positive rate:** benign control trials incorrectly blocked
    or flagged divided by benign control trials.
-   **Latency:** elapsed time from scenario submission to final
    response; gateway decision latency can also be measured separately.

Record the model and configuration, scenario/run ID, and trial outcome.
Keep configurations consistent when comparing results.

## Security and Repository Hygiene

Do not commit:

-   `.env` or any real API key
-   `.venv/`
-   `environment/portal.db`
-   `environment/portal.db.backup`
-   Other local database files or secrets

Commit `.env.example` with placeholder values only. If a real API key is
accidentally committed, revoke or rotate it; deleting it in a later
commit is not sufficient to remove it from repository history.

## Troubleshooting

-   **Port 8000 is in use:** stop the other service or coordinate a
    different host port.
-   **Container exits or restarts repeatedly:** run
    `docker compose logs --tail=100 app` and inspect the traceback.
-   **A new Python dependency is missing:** add it to `requirements.txt`
    and rebuild with `docker compose up -d --build`.
-   **Source changes do not reload:** check that the override is active
    with `docker compose config` and inspect application logs.
-   **Local and Docker audit histories differ:** this is expected
    because the local SQLite file and Docker named volume are separate.
-   **Database disappears:** check whether `docker compose down -v` was
    run or whether a different Compose project/volume is being used.

## Project Status and Next Steps

1.  Complete the security gateway's validation, authorization, risk
    policy, and safe dispatch.
2.  Integrate the adversarial agent and controlled attack-scenario
    runner.
3.  Add benign control cases and agree on evaluation metric definitions.
4.  Run end-to-end tests and calculate metrics from observed outcomes.
5.  Verify clean-clone setup, Docker health, dashboard behavior, and
    tests before the final demonstration.

See `docs/SECURITY_GATEWAY_INTEGRATION.md` for the detailed
implementation plan and coordination guidance for Persons 2 and 3.
