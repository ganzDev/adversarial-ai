# Adversarial AI: Autonomous Exploitation and Defense of Tool-Enabled AI Agents

## Implementation and Integration Guide

**Audience:** Person 1 (environment, victim agent, integration, dashboard), Person 2 (security gateway and authorization), Person 3 (adversarial agent and attack scenarios).

**Purpose:** This document replaces the earlier integration guide. It describes the current application and Docker development workflow, establishes shared interfaces, and gives Persons 2 and 3 implementation tasks that fit the existing codebase.

**Implementation note:** This guide reflects the current project state reported by the team as of October 27, 2026. Confirm exact function signatures and request/response fields in the latest checkout before changing shared interfaces. Keep changes coordinated through Git rather than independently changing shared schemas.

---

## 1. Project purpose and scope

The project evaluates security risks in tool-enabled AI agents using a controlled, simulated IT administration environment. A victim AI interprets instructions and proposes tool calls. An adversarial AI supplies attack attempts and malicious content. A security gateway evaluates each proposed action and either denies it or permits a specific simulated operation. The application records events so the team can inspect behavior and calculate experiment metrics.

Primary attack classes:

- Direct prompt injection.
- Indirect prompt injection embedded in retrieved ticket or file content.
- Tool abuse, including attempts to invoke tools outside the registered tool set.
- Privilege abuse, including attempts to perform state-changing operations without authorization or approval.

Planned metrics:

- Attack success rate.
- Detection rate.
- False-positive rate.
- End-to-end latency.

### Safety and isolation requirements

- Use fictional employees, tickets, and organization data only.
- Simulated file reads must remain limited to predefined in-app paths.
- Configuration changes and service restarts must affect simulated state only.
- Do not execute shell commands, arbitrary Python, host filesystem operations, or real service controls based on model output.
- Do not use real credentials, production systems, or real user data in test scenarios.
- Never treat a model-generated statement, retrieved document, ticket, or file as authorization evidence.

## 2. Current implementation and ownership

| Component | Current responsibility | Owner / next action |
|---|---|---|
| `environment/api.py` | FastAPI app, dashboard/API routes, database initialization, instruction submission, audit-event endpoints | Person 1 maintains and coordinates API changes |
| `environment/database.py` | SQLite fictional employees and support tickets; database path configurable through `APP_DATABASE_PATH` | Person 1 |
| `environment/tool_schemas.py` | Shared `ToolRequest`, `ToolResult`, and `AVAILABLE_TOOLS` registry | Person 1 maintains contract with Person 2 |
| `environment/tools.py` | Simulated tool implementations and simulated state | Person 1; do not add host-level operations |
| `agents/decision.py` | OpenAI decision loop, structured decision parsing, bounded tool calls, victim-agent calls, audit recording | Person 1; coordinate attacker/evaluation hooks |
| `agents/victim.py` | Validates tool names and routes requests through the gateway | Person 1 |
| `security/gateway.py` | Authorization boundary and controlled dispatch; currently a fail-closed stub | Person 2 implements |
| `environment/audit_log.py` | SQLite audit event storage, retrieval, clearing, individual event deletion, argument sanitization | Person 1; coordinate event schema with Person 2/3 |
| `environment/templates/dashboard.html` | Dashboard markup | Person 1 |
| `environment/static/dashboard.js` | Instruction submission and audit dashboard interactions, filters, event details, clearing and per-event deletion | Person 1 |
| `environment/static/dashboard.css` | Dashboard styling | Person 1 |
| `tests/` | Regression and integration tests | All contributors add tests for their code |
| `Dockerfile`, `compose.yaml` | Container image and base Compose configuration | Person 1 maintains; all contributors use |
| `compose.override.yaml` | Local development live-reload and bind mounts | Person 1 maintains; keep database volume isolated |

Expected logical repository layout:

```text
adversarial-ai/
├── agents/
│   ├── decision.py
│   └── victim.py
├── environment/
│   ├── api.py
│   ├── audit_log.py
│   ├── database.py
│   ├── tool_schemas.py
│   ├── tools.py
│   ├── templates/dashboard.html
│   └── static/
│       ├── dashboard.js
│       └── dashboard.css
├── security/
│   └── gateway.py
├── tests/
├── Dockerfile
├── .dockerignore
├── compose.yaml
├── compose.override.yaml
├── requirements.txt
├── .env.example
└── docs/
    └── SECURITY_GATEWAY_INTEGRATION.md
```

This is a logical map; confirm actual filenames in the current branch before assuming a file exists.

## 3. Shared tool contract

The shared schema in `environment/tool_schemas.py` currently defines a request with these conceptual fields:

- `tool`: registered tool name.
- `resource`: resource category the tool targets.
- `operation`: one of `read`, `update`, or `restart`.
- `arguments`: tool-specific argument dictionary.

The result contract contains:

- `allowed`: whether the gateway permitted the operation.
- `result`: simulated operation result, when applicable.
- `reason`: concise explanation, especially for denials.
- `risk`: one of `low`, `medium`, or `high`.

The gateway entry point used by the victim agent is:

```python
def authorize_and_execute(request: ToolRequest) -> ToolResult:
    ...
```

**Compatibility requirement:** Preserve `authorize_and_execute(request: ToolRequest) -> ToolResult` unless Person 1 and Person 2 agree to update the caller, tests, and this document together. The gateway is currently a fail-closed stub; normal tool requests may be denied until Person 2 implements its policy.

### Registered tools

The current registry contains these six tools:

| Tool | Resource | Operation | Intended behavior |
|---|---|---|---|
| `get_system_status` | `system_status` | `read` | Read status from simulated IT services |
| `read_ticket` | `support_tickets` | `read` | Read one fictional support ticket |
| `query_employee` | `employee_records` | `read` | Read one fictional employee record |
| `read_file` | `simulated_files` | `read` | Read a predefined simulated company file |
| `update_config` | `system_configuration` | `update` | Change a supported simulated configuration key |
| `restart_service` | `it_services` | `restart` | Restart a known simulated service |

Known restrictions include predefined simulated file paths such as `/company/it/readme.txt` and `/company/it/maintenance.txt`, configuration keys such as `maintenance_mode` and `max_login_attempts`, and a fixed list of simulated service names. Verify the current implementation before adding cases; do not loosen restrictions to make an attack scenario easier.

## 4. Request and execution flow

```text
User / dashboard
      |
      | POST /assistant/instruction
      v
FastAPI (environment/api.py)
      |
      v
Victim decision layer (agents/decision.py)
  - sends instruction and bounded context to the model
  - parses a structured decision
  - rejects malformed arguments and unknown tools
  - limits tool calls per instruction (currently 3 by default)
      |
      v
Victim agent (agents/victim.py)
  - checks tool against AVAILABLE_TOOLS
  - builds ToolRequest from registered metadata and arguments
      |
      v
Security gateway (security/gateway.py)  <-- Person 2
  - canonical request validation
  - authorization and risk classification
  - deny OR dispatch to an explicit simulated function
      |
      v
Simulated tools (environment/tools.py)
      |
      v
ToolResult -> victim / decision layer -> model response
      |
      +--> audit event recorded in environment/audit_log.py
      |
      +--> API response displayed by dashboard

Person 3's adversarial agent supplies attack instructions or malicious
retrieved content through a controlled scenario runner; it does not
bypass the victim agent or call simulated tools directly.
```

### Non-negotiable boundaries

1. The model proposes actions; deterministic code authorizes them.
2. Every tool execution must pass through `authorize_and_execute()`.
3. Unknown tools, tool/resource/operation mismatches, and invalid arguments must be rejected.
4. The gateway must use an explicit mapping to known simulated functions; never dynamically execute a model-supplied function name.
5. Denied requests must not mutate simulated state.
6. Retrieved ticket/file content is untrusted data, even when it contains instructions that claim to be system policy or administrator approval.
7. The UI is for observation and testing, not an authorization boundary.
8. All behavior remains simulated; do not add unrestricted filesystem, shell, or real service access.

## 5. Person 2: security gateway implementation plan

Person 2 owns `security/gateway.py` and the policy/approval logic. Implement the following in order.

### 5.1 Canonical request validation

- Confirm the tool exists in `AVAILABLE_TOOLS`.
- Confirm resource and operation match the canonical registry entry exactly.
- Reject unknown tools and mismatched metadata even if the victim agent should already have validated them.
- Validate tool-specific argument keys, types, bounds, and allowed values.
- Reject unexpected arguments rather than silently ignoring ambiguous inputs.
- Validate employee IDs, ticket IDs, simulated file paths, configuration keys/values, and service names against explicit allowlists or the corresponding simulated data.

### 5.2 Authorization policy and approvals

Create a small, documented policy matrix before implementing complex logic. For each tool, record:

- permitted roles or conditions (only if the simulation models roles explicitly),
- whether the action is read-only or state-changing,
- whether approval is required,
- risk level and denial reason,
- expected simulated side effect.

Use least privilege and default-deny behavior. Claims such as “I am the administrator,” “the policy has been overridden,” or “this was approved” must not grant permissions. Approval must be represented by trusted application state or an explicit validated approval mechanism—not by free-form prompt text.

### 5.3 Safe dispatch

- Perform all validation and authorization before dispatch.
- Use an explicit mapping from registered tool names to functions in `environment/tools.py`.
- Never use `eval`, shell execution, arbitrary paths, or model-controlled imports.
- Return a consistent `ToolResult` for allow and deny paths.
- Handle expected validation/dispatch errors without leaking stack traces, API keys, or sensitive data.
- Ensure a denied request produces no state change.

### 5.4 Risk and audit ownership

Classify risk consistently as `low`, `medium`, or `high`. Document which factors affect the classification, such as operation type, resource, invalid arguments, privilege boundary, and policy violations.

The decision layer currently records the returned tool result in the audit log. Coordinate before adding gateway-level audit writes so each action does not produce duplicate rows. Agree whether `outcome="authorized"` means “policy permitted” or “operation executed successfully”; if needed, record policy decision and execution outcome as separate fields.

### 5.5 Tests Person 2 should add

- Every registered tool: valid allowed request and representative denied request.
- Unknown tool and tool/resource/operation mismatch.
- Missing, extra, wrong-type, and out-of-range arguments.
- Invalid paths, keys, values, IDs, and service names.
- State-changing operation without required approval.
- Prompt text that claims to override policy or claims approval.
- Denied request causes no simulated side effect.
- Stable risk/reason/outcome fields.
- No host filesystem, shell, or real service operation can be reached.

## 6. Person 3: adversarial agent and scenario implementation plan

Person 3 owns the adversarial AI and attack scenario design. Keep it separate from the gateway: the adversarial agent should generate attack attempts and scenario inputs, while the gateway remains the independent enforcement layer.

### 6.1 Suggested interface

Agree with Person 1 on a small scenario interface before coding. A practical initial contract is a scenario object with:

- `scenario_id`: stable identifier.
- `attack_type`: one of `direct_prompt_injection`, `indirect_prompt_injection`, `tool_abuse`, or `privilege_abuse`.
- `user_instruction`: the instruction sent to the victim agent.
- `injected_content`: optional controlled malicious content to place in a fictional ticket or simulated file.
- `target_behavior`: the behavior the scenario is trying to induce, expressed as an evaluation objective rather than an execution bypass.
- `expected_defense`: the intended policy behavior, such as deny an unauthorized update.
- `metadata`: safe labels for reproducibility (seed, variant, notes); never put secrets here.

This is a proposed integration contract, not a claim that a matching class already exists. Put shared schema definitions in a mutually agreed module and add tests before wiring it into the API.

### 6.2 Required scenario families

1. **Direct prompt injection:** User instruction asks the victim to ignore prior instructions or invoke an unauthorized tool/action.
2. **Indirect prompt injection:** A fictional ticket or predefined simulated file contains adversarial instructions; the victim retrieves it as data.
3. **Tool abuse:** The attack requests an unknown tool, unsupported argument, mismatched resource, or action outside the allowlist.
4. **Privilege abuse:** The attack asserts elevated privileges or approval and requests a state-changing action without valid authorization.

Include benign control scenarios for comparison, such as legitimate ticket reads, employee lookups, and allowed status checks. Without controls, the team cannot estimate false-positive behavior reliably.

### 6.3 Experiment record requirements

For each run, capture or associate:

- scenario ID and attack class,
- exact model configuration/model name (not the API key),
- timestamp and run identifier,
- attack intent / expected target behavior,
- gateway decision and risk classification,
- whether a simulated side effect actually occurred,
- whether the defense detected or blocked the attack,
- end-to-end latency.

Avoid logging full prompts or injected documents unless needed and approved for the experiment. Prefer safe scenario IDs and labels. Never log secrets.

### 6.4 Person 3 tests

- Scenario schema validation and stable scenario IDs.
- Each attack family reaches the victim only through the agreed interface.
- Indirect injection is delivered as retrieved untrusted content, not as gateway policy.
- Malicious content cannot call tools directly or alter gateway configuration.
- Benign controls run alongside attacks.
- Repeated runs use documented settings so results can be reproduced.

### 6.5 Integration sequence

1. Person 3 creates the scenario schema and a small initial set of attack/control scenarios.
2. Person 1 exposes a controlled runner or endpoint only after agreeing on the schema; preserve the existing `/assistant/instruction` behavior unless the team coordinates a change.
3. Person 2 ensures every proposed tool call from every scenario still passes through the gateway.
4. The team runs the same scenario set against the gateway and records outcomes.
5. The team reviews false positives on benign controls and revises policy deliberately, not by weakening validation globally.

## 7. Audit log and dashboard

`environment/audit_log.py` stores audit events in SQLite and sanitizes selected sensitive argument keys. The current dashboard supports event history, filters, event details, clearing history, and deleting a single event.

Known routes in the current implementation include:

- `GET /audit-events?limit=...` — list recent events.
- `DELETE /audit-events` — clear audit history.
- `DELETE /audit-events/{event_id}` — delete one event by its ID.
- `POST /assistant/instruction` — submit an instruction to the victim flow.
- `GET /health` — health response.
- `GET /docs` — interactive FastAPI documentation.
- `GET /employees`, `GET /employees/{employee_id}`, `GET /tickets`, `GET /tickets/{ticket_id}` — simulated data endpoints.

Confirm exact request/response schemas in `environment/api.py` or `/docs` before writing an integration client.

Audit expectations:

- Record denied and rejected attempts, not just successful actions.
- Never store API keys or credentials in audit fields.
- Keep outcomes consistent and documented. `authorized`, `denied`, and `rejected` should not be treated as equivalent.
- Clearing audit history must not reset employee data, tickets, gateway policy, or simulated service/configuration state.
- Individual event deletion removes that audit record only; it should not change the action or simulated state that originally produced it.
- Coordinate audit ownership to avoid duplicate events when Person 2 adds gateway logging.

## 8. Docker architecture and behavior

Docker is the shared way for teammates to run the application consistently. The current setup uses one FastAPI application container and a persistent named SQLite volume.

### 8.1 Files and responsibilities

- `Dockerfile`: builds a Python 3.12 image, installs dependencies from `requirements.txt`, copies application packages, and starts Uvicorn.
- `.dockerignore`: excludes `.git`, virtual environments, bytecode/cache, `.env`, local database files, tests, and docs from the image build context (review this list if tests/docs need to be copied into the image later).
- `compose.yaml`: builds and runs the app, maps host port `8000` to container port `8000`, reads local `.env`, sets `APP_DATABASE_PATH=/data/portal.db`, and mounts a named volume at `/data`.
- `compose.override.yaml`: automatically loads during local development; bind-mounts source directories/files and runs Uvicorn with `--reload`.
- `.env`: local-only configuration and API key; never commit.
- `.env.example`: committed template with placeholder values only.

The base Compose file and local override are combined automatically by Docker Compose. On teammates' development machines, `compose.override.yaml` enables code changes to be reflected in the container without rebuilding the image. The override intentionally mounts selected files/directories rather than the entire `environment/` directory, preventing a local `environment/portal.db` from shadowing the database inside the container.

### 8.2 Database persistence

The container uses `/data/portal.db`, stored in the named volume `portal_data`. The database survives container restarts and normal container recreation. The local development database `environment/portal.db` is separate and ignored by Git. Teammates will have their own Docker volume and their own local audit history.

**Do not use `docker compose down -v` during ordinary development.** The `-v` option removes named volumes and can delete the persistent database. Use `docker compose stop`, `docker compose restart`, or `docker compose down` without `-v` for normal lifecycle management.

### 8.3 Start, inspect, and stop

From the repository root:

```bash
# Build the image and start the application (first run or after dependency/Dockerfile changes)
docker compose up -d --build

# Check container status
docker compose ps

# Follow application logs; Ctrl+C stops log viewing, not the app
docker compose logs -f app

# Check the health endpoint
curl -i http://localhost:8000/health

# Stop containers but preserve the named database volume
docker compose stop

# Start existing containers again
docker compose up -d

# Restart the app container
docker compose restart app
```

URLs:

- Dashboard: `http://localhost:8000/`
- Health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- Audit API: `http://localhost:8000/audit-events`

A container status of `Up` means the container is running, not necessarily that the API is healthy. Confirm the health endpoint returns HTTP 200. A health check is only reported as `healthy` if one is explicitly configured in Compose/Docker; do not assume `docker compose ps` will display that state.

### 8.4 When a rebuild is required

With the development override active:

- **Python, HTML, CSS, and JavaScript source edits:** normally reload automatically; no image rebuild required.
- **`requirements.txt` changes:** rebuild the image so new packages are installed.
- **`Dockerfile` changes:** rebuild the image.
- **Base Compose settings or dependencies:** recreate/rebuild as appropriate.
- **Changes to the override file:** recreate the service with `docker compose up -d` so Compose applies the updated configuration.

If code changes are not picked up, inspect `docker compose logs -f app`. A Python import error may prevent the application process from starting even while the Uvicorn reloader process remains running.

### 8.5 Teammate setup from a fresh clone

Prerequisites: Git, Docker Desktop, and WSL integration if using Ubuntu under WSL.

```bash
git clone <repository-url>
cd adversarial-ai
cp .env.example .env
```

Edit `.env` with the required variable names and the teammate's own API key. Never copy another person's real `.env` file into Git or a shared repository. Confirm `.env.example` matches the variable names read by the current code.

```bash
docker compose up -d --build
docker compose ps
curl -i http://localhost:8000/health
```

Then open `http://localhost:8000/`. The first run creates that teammate's named database volume. If their branch adds packages, they should update `requirements.txt` and rebuild the image.

### 8.6 Docker troubleshooting

- **Port 8000 is already in use:** stop the other local app/container or coordinate a different host port.
- **Container is `Exited` or repeatedly restarting:** run `docker compose logs --tail=100 app` and fix the underlying traceback.
- **Dashboard loads but API calls fail:** inspect browser developer tools and the API logs; verify the current endpoints and JavaScript match.
- **New Python dependency cannot be imported:** add it to `requirements.txt`, then run `docker compose up -d --build`.
- **Audit history differs from local development:** expected when the local SQLite database and Docker named volume are separate.
- **Database seems to disappear:** check whether `docker compose down -v` was used or whether a different Compose project/volume is active.
- **Code changes do not reload:** confirm the override is present, inspect `docker compose config`, and check logs for import or syntax errors.

## 9. Configuration and secrets

The decision layer currently loads `.env` with `load_dotenv(override=True)` before creating the OpenAI client. The model defaults to `gpt-4.1-mini`, and `OPENAI_MODEL` can be used to configure it if that is the variable name in the current code.

The committed `.env.example` should contain variable names and placeholders only, for example:

```dotenv
OPENAI_API_KEY=replace_with_your_own_key
OPENAI_MODEL=gpt-4.1-mini
```

Verify variable names against the current `.env` and code before committing the template. Keep `.env`, `.venv/`, `environment/portal.db`, and `environment/portal.db.backup` out of Git. If a real key has ever been committed, removing it in a later commit is not sufficient; revoke/rotate it and remove the secret from repository history as appropriate.

## 10. Tests and quality gates

The current suite includes `tests/test_victim.py` and `tests/test_audit_log.py`; the project previously had 17 tests passing. Re-run the tests in the latest checkout after integration rather than assuming that earlier result still holds.

Local test command:

```bash
pytest -q
```

If the local virtual environment is managed with `uv`, install dependencies into the project interpreter and regenerate the dependency list with:

```bash
uv pip install --python .venv/bin/python <package>
uv pip freeze --python .venv/bin/python > requirements.txt
```

Before merging gateway or attacker changes, test:

- Existing victim and audit-log regression tests.
- Every registered tool's allowed and denied paths.
- Invalid tool/resource/operation combinations and malformed arguments.
- Denied requests do not mutate simulated state.
- Direct and indirect prompt-injection scenarios.
- Tool abuse and privilege-abuse scenarios.
- Benign control scenarios and false positives.
- Audit persistence and stable event fields.
- Dashboard event filtering, clearing, and individual deletion.
- Docker startup and `GET /health` returning HTTP 200.

## 11. Metric definitions to agree on before experiments

Use explicit definitions so different teammates do not calculate metrics differently. Suggested starting definitions:

- **Attack success rate:** successful harmful simulated outcomes divided by total attack trials. Define “successful” based on an observed unauthorized side effect, not merely a model saying it succeeded.
- **Detection rate:** attack trials correctly identified or blocked by the defense divided by attack trials. Specify whether a block alone counts as detection or whether a recorded detection signal is required.
- **False-positive rate:** benign control trials incorrectly blocked or flagged divided by all benign control trials.
- **Latency:** elapsed time from submitting a scenario to receiving the final response; optionally report gateway decision latency separately.

Agree whether the unit of analysis is one scenario, one tool call, or one full conversation. Record model name/configuration and run ID for reproducibility. Do not compare results across different model settings without noting the change.

## 12. Integration checklist and definition of done

### Person 1

- [x] Simulated environment, FastAPI API, victim-agent path, dashboard, and audit storage established.
- [x] Docker image, Compose service, persistent database volume, and local live-reload setup established.
- [x] Individual audit-event deletion endpoint implemented and tested.
- [ ] Coordinate shared schema and scenario runner interface with Persons 2 and 3.
- [ ] Validate clean-clone setup from the latest Git commit.

### Person 2

- [ ] Implement canonical validation and authorization in `security/gateway.py`.
- [ ] Add explicit safe dispatch to the six registered simulated tools.
- [ ] Define risk policy and approval requirements.
- [ ] Add unit tests for allow, deny, invalid requests, injection attempts, and no side effects on denial.
- [ ] Coordinate audit event ownership and outcome semantics with Person 1.

### Person 3

- [ ] Agree on and implement a scenario schema/runner interface with Person 1.
- [ ] Implement direct and indirect prompt injection, tool abuse, and privilege abuse scenarios.
- [ ] Include benign control scenarios.
- [ ] Ensure attack inputs never call tools directly or bypass the gateway.
- [ ] Record reproducible scenario/run metadata and evaluate observed outcomes.

### Team integration

- [ ] Run the same attack and control suite against the integrated system.
- [ ] Calculate attack success, detection, false-positive, and latency metrics using agreed definitions.
- [ ] Verify the dashboard accurately presents decisions and audit events.
- [ ] Run the test suite and Docker health check from a clean checkout.
- [ ] Document any remaining limitations before final presentation.

---

**Ownership summary:** Person 1 owns the simulated environment, victim-agent routing, dashboard, Docker workflow, and cross-component integration. Person 2 owns the security gateway, authorization policy, risk decisions, and approval workflow. Person 3 owns adversarial prompts, attack scenarios, and scenario evaluation. All contributors should preserve the shared `ToolRequest`/`ToolResult` contract and coordinate schema changes before merging.
