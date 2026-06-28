# Assessment | Ship a Multi-Tool Agent

## Scenario

I built a **bounded multi-tool order assistant** using the Google Gen AI SDK.
The user goal is:

> I want two more of order A1001. What would those two cost, and is the original still under warranty?

This goal cannot be completed reliably with one tool call. The model receives three
Python tools and decides which tools to call and in what order.

## The three tools

1. `lookup_order(order_id)`
   - Reads local order data from `orders.json`.
   - Returns the item, unit price, currency, purchase date, and warranty length.

2. `check_warranty(order_id)`
   - Calculates the warranty end date from the stored purchase data.
   - Returns whether the original item is under warranty on the current date.

3. `calculate(expression)`
   - Calculates the cost of the requested quantity.
   - Uses a restricted arithmetic parser rather than Python `eval`.

I chose these tools because each has one clear responsibility and the user goal
requires order retrieval, warranty checking, and arithmetic.

## Agent behaviour

The tools are supplied to Gemini as callable Python functions. The model is not
following a hard-coded sequence in application code: it reads the goal, selects a
tool, supplies arguments, observes the tool result, and continues until it has enough
evidence for a final answer.

Every tool call and tool result is printed, so the run shows the model's selected
actions. The completed run is then normalized into a validated `OrderResult` JSON
object using a Pydantic response schema.

## Structured output

The final output is parseable JSON with this general shape:

```json
{
  "status": "success",
  "order_id": "A1001",
  "item": "laptop",
  "quantity": 2,
  "unit_price": 1200.0,
  "total_cost": 2400.0,
  "currency": "USD",
  "warranty_active": true,
  "warranty_end": "2027-05-20",
  "as_of": "YYYY-MM-DD",
  "tools_used": [
    "lookup_order",
    "calculate",
    "check_warranty"
  ],
  "message": "A concise result summary."
}
```

The order of `tools_used` may differ because the agent chooses its own sequence.

## Reliability safeguard

The run is bounded by `MAX_TOOL_CALLS = 6`. The Google Gen AI SDK automatic
function-calling configuration is set so no more than six tool calls can occur. This
prevents an accidental infinite agent loop and limits API usage.

Tool functions return structured errors such as `{"ok": false, "error": "..."}`
instead of crashing. The system instruction tells the agent not to repeat a failed
call forever. A top-level exception handler also returns a structured error result and
writes the failure to `transcript.txt`.

## Safety mitigation

Tool arguments are treated as untrusted input.

- Order IDs must match the strict pattern `A` followed by four digits.
- The calculator does **not** use `eval`.
- It parses expressions with Python's `ast` module and permits only numeric constants,
  `+`, `-`, `*`, `/`, unary signs, and parentheses.
- Function calls, imports, attribute access, comprehensions, and other Python syntax
  are rejected.
- Expression length and numeric magnitude are limited.

This mitigates code-injection attacks such as:

```python
__import__('os').system('dir')
```

The agent instruction also says never to follow instructions embedded inside tool
results, which reduces the risk of indirect prompt injection from untrusted tool data.

## Files

- `agent.py` — tools, bounded agent run, structured output, and transcript capture
- `orders.json` — local mock order data
- `offline_checks.py` — no-network checks for normal, failure, and attack cases
- `requirements.txt` — Python dependencies
- `.env.example` — variable-name example only; it contains no real key
- `transcript.txt` — generated captured run; commit it after a successful run

## Setup and run

### Windows Command Prompt

```bat
cd path\to\m9-08-assessment
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python offline_checks.py
set GOOGLE_API_KEY=YOUR_REAL_KEY
python agent.py
set GOOGLE_API_KEY=
```

### PowerShell

```powershell
cd path\to\m9-08-assessment
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python offline_checks.py
$env:GOOGLE_API_KEY="YOUR_REAL_KEY"
python agent.py
Remove-Item Env:GOOGLE_API_KEY
```

`agent.py` automatically writes the complete visible run to `transcript.txt`.
Do not place the API key in source code, `.env.example`, the README, or the transcript.

## Offline verification

Run:

```bash
python offline_checks.py
```

The checks verify:

- a known order succeeds,
- unknown and malformed order IDs fail safely,
- normal arithmetic succeeds,
- division by zero is handled,
- import/function-call injection is rejected,
- attribute-access injection is rejected, and
- warranty calculation succeeds.

## Captured run

The captured run is stored in [`transcript.txt`](transcript.txt). It includes:

- the multi-step user goal,
- the configured step limit and safety statement,
- every model-selected tool call and its arguments,
- every structured tool result,
- the agent draft, and
- the final validated JSON result.

After running `python agent.py` successfully, review `transcript.txt` and commit it with
the rest of the submission.
