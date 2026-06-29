# MVP Design — Session-by-Session Build Plan (Stage 2)

> **Purpose:** Divide the SliceMatic Stage 2 Gradio MVP into small, self-contained **sessions**, each executed by a fresh Sonnet session (via a future `create-spec` skill). Every session is scoped so the executing model needs only this document + the named source files — not the prior session's reasoning.
> **Source of truth:** [`STAGE2_PLAN.md`](./STAGE2_PLAN.md) (approach), [`PizzaFlow_Assignment_Brief_FDE.md`](./PizzaFlow_Assignment_Brief_FDE.md) (spec), [`SliceMatic_Business_Economics.md`](./SliceMatic_Business_Economics.md) §7 (golden bill).
> **Scope:** Stage 2 only. Stage 3 (Vercel/Supabase/AI) is out of scope.

---

## 1. How to use this document

- Sessions are **sequential and dependency-ordered** (S1 → S8). Each session **branches off `main`** *after* the previous session has merged. Because no two branches are open at once, sessions that both extend `core.py`/`test_core.py` never conflict.
- Each session below is a complete spec: **Objective · Reasoning · Prerequisites · Files · Tasks · Interface produced · Acceptance · Definition of Done**. Feed one session block to `create-spec` to generate that session's branch + spec.
- The **§4 Contracts** section is *frozen*: function signatures and data shapes are fixed up front so any session can call/produce them without reading another session's code. If a session needs to change a contract, that is a doc change first.

### Conventions

| Item | Convention |
|---|---|
| Python | 3.10–3.12 |
| Gradio | `gradio==5.49.1` (pin exactly; bare install pulls breaking 6.x) |
| Branch | `feat/0N-short-name` (e.g. `feat/02-menu-parser`) |
| Commits | Conventional (`feat:`, `test:`, `chore:`); commit at each working checkpoint |
| Test command | `pytest -q` (logic sessions); `python app.py` + browser (UI sessions) |
| Merge | Fast-forward / merge the session branch into `main` before starting the next session |
| Money | `float` + `round(…, 2)`; never hardcode menu data |

---

## 2. Architecture & file layout

```
core.py            # PURE logic — no gradio import. Parser, validators, pricing, bill HTML, persistence.
app.py             # Gradio shell — imports core, builds the wizard, wires handlers. No business logic.
test_core.py       # pytest — golden bill, 8 edge cases, parser fixtures, log round-trip.
requirements.txt   # gradio==5.49.1, pytest
.gitignore
README.md          # short: run + test instructions
Types_of_Base.txt  Types_of_Pizza.txt  Types_of_Toppings.txt   # provided; grader swaps
orders_log.txt     # generated sample (deliverable)
```

**Principle (from STAGE2_PLAN §9.1):** all testable logic lives in `core.py` as pure functions; `app.py` is a thin shell. This makes the 8-point validation surface and the golden bill verifiable with `pytest` and no browser, and isolates UI bugs from logic bugs.

---

## 3. Dependency graph (build order)

```
S1 Setup/scaffold
        │
S2 Menu parser ───┐
S3 Validators ────┤  (all extend core.py + test_core.py, sequentially)
S4 Pricing+BillHTML┤
S5 Persistence ───┘
        │
S6 Gradio shell + navigation skeleton  (creates app.py)
        │
S7 Wire validation/pricing/logging into handlers + menu display + error banner
        │
S8 Integration · sample log · browser verification · packaging
```

S2–S5 are logic-only and could in principle be reordered, but the listed order matches natural dependency (pricing references the menu item shape; persistence references the bill shape).

---

## 4. Frozen contracts (the interface every session builds to)

### 4.1 Data shapes

```python
# A menu item (output of load_menu)
Item = {"id": str, "name": str, "price": float}

# The accumulating order dict carried in gr.State and consumed by log_order
Order = {
    "session_start": str,   # ISO-8601, seeded by demo.load
    "name": str,            # validated
    "phone": str,           # validated, 10 digits
    "qty": int,             # 1..10
    "base": Item, "pizza": Item, "topping": Item,
    "bill": Bill,           # see compute_bill output
    "payment": str,         # "Cash" | "Card" | "UPI"
    "timestamp": str,       # ISO-8601, stamped at log time (order completion)
}

# Bill = output of compute_bill
Bill = {
    "unit_price": float, "quantity": int,
    "subtotal": float, "discount": float, "post_discount": float,
    "gst": float, "total": float, "discount_applied": bool,
}
```

### 4.2 `core.py` function signatures (frozen)

```python
class MenuError(Exception): ...                      # missing file / zero valid items

def load_menu(path: str) -> list[Item]: ...
    # Defensive parse of "ID;Name;Price" per STAGE2_PLAN §3.
    # Skips blank/malformed/non-numeric/non-positive lines.
    # Raises MenuError if the file is missing OR yields zero valid items.

def validate_name(raw: str)  -> tuple[bool, str]:        ...  # (True, clean) | (False, msg)
def validate_phone(raw: str) -> tuple[bool, str]:        ...  # (True, phone) | (False, msg)
def validate_qty(raw: str)   -> tuple[bool, "int|str"]:  ...  # (True, qty)   | (False, msg)
def validate_choice(raw: str, n: int) -> tuple[bool, "int|str"]: ...  # (True, 1..n) | (False, msg)
def validate_payment(raw: str) -> tuple[bool, str]:      ...  # (True, "Cash"/"Card"/"UPI") | (False, msg)

def compute_bill(base: Item, pizza: Item, topping: Item, qty: int) -> Bill: ...
def render_bill_html(bill: Bill, name: str) -> str: ...   # styled invoice (STAGE2_PLAN §6)

def format_order_record(order: Order) -> str: ...         # single pipe-separated line (no trailing blank)
def log_order(order: Order, path: str = "orders_log.txt") -> None: ...  # lock-guarded append + blank-line separator

PAYMENT_MODES = {"1": "Cash", "2": "Card", "3": "UPI"}
def payment_confirmation(mode: str, total: float) -> str: ...   # per-mode message
```

**Error-message text** comes verbatim from STAGE2_PLAN §2 (the validators return those exact strings).

**Validator return convention:** `(ok, payload)`. On success `payload` is the cleaned/typed value; on failure `payload` is the user-facing error string. `app.py` does: `ok, val = validate_x(raw); if not ok: raise gr.Error(val)`.

---

## 5. Sessions

### S1 — Project setup & scaffold
- **Branch:** `feat/01-setup`
- **Objective:** Initialize the repo and create the empty module skeleton + tooling so later sessions have a runnable foundation.
- **Reasoning:** A clean scaffold means every later session starts from `pytest` green (0 tests) and importable modules — no environment debugging mid-feature. Git history from S1 onward also seeds the commit trail Stage 3 requires.
- **Prerequisites:** none.
- **Reads:** this doc §2, §4.
- **Creates:** `git init`; `requirements.txt` (`gradio==5.49.1`, `pytest`); `.gitignore` (`__pycache__/`, `*.pyc`, `.venv/`, `flagged/`); `core.py` (module docstring + `class MenuError(Exception): pass` + the frozen signatures as stubs raising `NotImplementedError`); `app.py` (stub with `if __name__ == "__main__":` guard); `test_core.py` (imports core, one trivial `test_import` that passes); `README.md` (run/test instructions skeleton). Confirm the 3 `Types_of_*.txt` files exist.
- **Tasks:** create venv-agnostic files; ensure `pip install -r requirements.txt` resolves; ensure `python -c "import core, app"` succeeds; ensure `pytest -q` passes.
- **Interface produced:** the stub signatures from §4.2 (all raise `NotImplementedError`).
- **Acceptance:** `pytest -q` green; `python -c "import core, app"` exits 0; `git log` shows the scaffold commit.
- **DoD:** commit, merge to `main`.

### S2 — Menu parser (`core.load_menu`)
- **Branch:** `feat/02-menu-parser`
- **Objective:** Implement the defensive `ID;Name;Price` parser and its full fixture test suite.
- **Reasoning:** Menu loading is 6 rubric points and the grader swaps the files — robustness here is non-negotiable. Building it first gives later sessions real `Item` data to price and display.
- **Prerequisites:** S1.
- **Reads:** STAGE2_PLAN §3 (parsing rules + fixtures), §4 contracts.
- **Modifies:** `core.py` (`load_menu`, `MenuError`); `test_core.py` (parser tests).
- **Tasks:** implement per §3 — UTF-8 read; per-line strip; skip blanks; `split(";")`; `<3` parts skip; `>3` parts → `id=parts[0]`, `price=parts[-1]`, `name=";".join(parts[1:-1])`; empty id/name skip; `float(price)` in try/except, non-numeric skip; `price<=0` skip. Raise `MenuError` on `FileNotFoundError` or zero valid items. Write fixture files under a temp dir (or use `tmp_path`) covering: trailing newline, blank middle line, `B6;Stuffed;` (no price), `B7;;199` (no name), `B8;Weird;Name;199` (extra `;` → name "Weird;Name"), `B9;Bad;abc` (non-numeric), `B10;Neg;-50` (negative), fully empty file (→ MenuError), missing file (→ MenuError). Also assert the **provided** `Types_of_*.txt` parse to the expected counts (5 bases, 8 pizzas, 10 toppings).
- **Interface produced:** `load_menu`, `MenuError`.
- **Acceptance:** all parser fixture tests + provided-file count tests pass under `pytest -q`.
- **DoD:** commit, merge.

### S3 — Validators (`core.validate_*`)
- **Branch:** `feat/03-validators`
- **Objective:** Implement the five pure validators and a test that exercises all 8 mandated edge cases.
- **Reasoning:** This is the 8-point line and the single biggest scoring risk. Pure functions let us prove every edge case in `pytest` before any UI exists.
- **Prerequisites:** S1 (independent of S2; ordered for cohesion).
- **Reads:** STAGE2_PLAN §2 (rules + exact error strings + the 8-case map), §4 contracts.
- **Modifies:** `core.py` (validators); `test_core.py` (edge-case tests).
- **Tasks:** implement `validate_name` (strip; letters+spaces only; 2–40; ≥1 letter), `validate_phone` (strip; exactly 10 digits; first ∈ {6,7,8,9}), `validate_qty` (strip; `re.fullmatch(r"\d+", s)` then int; 1–10; reject `2.5`/`three`/`0`/`11`/empty), `validate_choice(raw, n)` (strip; digits-only; 1..n; rejects 0, >n, a price like 229, letters, empty), `validate_payment` (strip; ∈ {"1","2","3"} → mode name). Return the exact §2 error strings. Tests must explicitly cover all 8 edge cases (name-only-spaces; phone starting 1; qty 0 & 11; choice 0 & >n; **price-as-item-number #5**; empty at every field #6; **non-integer qty "three"/"2.5" #7**) and assert both the boolean and the message.
- **Interface produced:** the five validators (§4.2).
- **Acceptance:** all 8 edge-case tests pass; boundary tests (qty 1, qty 10; choice 1, choice n) pass.
- **DoD:** commit, merge.

### S4 — Pricing engine + bill HTML (`core.compute_bill`, `core.render_bill_html`)
- **Branch:** `feat/04-pricing`
- **Objective:** Implement the pricing calculation and the HTML invoice renderer, verified against the golden bill.
- **Reasoning:** 7 rubric points; correctness is checkable exactly against the economics-doc sample. Bundling the (pure, string-returning) HTML renderer here keeps the UI session light and lets us assert invoice contents without a browser.
- **Prerequisites:** S2 (uses `Item` shape).
- **Reads:** STAGE2_PLAN §4 (calc order + golden bill), §6 (bill rendering), §4 contracts.
- **Modifies:** `core.py` (`compute_bill`, `render_bill_html`); `test_core.py` (pricing + render tests).
- **Tasks:** implement the exact calc order — `unit = base+pizza+topping`; `subtotal = unit*qty`; `discount = round(subtotal*0.10,2)` iff `qty>=5` else `0.00`; `post_discount = subtotal-discount`; `gst = round(post_discount*0.18,2)`; `total = round(post_discount+gst,2)`; set `discount_applied`. `render_bill_html` returns a `<table>` invoice with ₹ symbol, right-aligned amounts, line items (base/pizza/topping, unit price, qty, subtotal) and a footer block (Subtotal / Discount / GST 18% / **Total** bold). Tests: the **golden bill** (Cheese Burst 229 + BBQ Chicken 379 + Extra Cheese 69, qty 5 → total **3594.87**, gst 548.37, discount 338.50); discount boundary (qty 4 → discount 0.00; qty 5 → 10%); a no-discount case; assert `render_bill_html` output contains `₹3594.87`, `Subtotal`, `Discount`, `GST`, `Total`.
- **Interface produced:** `compute_bill`, `render_bill_html`.
- **Acceptance:** golden bill exact; boundary + render-content tests pass.
- **DoD:** commit, merge.

### S5 — Order persistence (`core.format_order_record`, `core.log_order`)
- **Branch:** `feat/05-persistence`
- **Objective:** Implement the orders-log record format and the lock-guarded append writer, with a round-trip parse test.
- **Reasoning:** 5 rubric points; the format must be parseable and append-correct (not overwrite). Testing the format as a pure string function avoids flaky file tests.
- **Prerequisites:** S4 (uses `Bill`), S3 (uses cleaned fields).
- **Reads:** STAGE2_PLAN §5 (format + example), §4 contracts.
- **Modifies:** `core.py` (`format_order_record`, `log_order`, module-level `threading.Lock`, `payment_confirmation`, `PAYMENT_MODES`); `test_core.py` (log tests).
- **Tasks:** `format_order_record(order)` → one line of pipe-separated `key=value` fields exactly per §5 (`timestamp | name | phone | base=ID:Name:Price | pizza=… | topping=… | unit_price | quantity | subtotal | discount | gst | total | payment`); money fields with 2 decimals. `log_order` → under a `threading.Lock`, open `path` in append mode (UTF-8, create if absent), write `record + "\n\n"` (blank line between orders), wrapped in try/except. `payment_confirmation(mode, total)` → per-mode strings (Cash: pay to rider on delivery; Card: payment confirmed; UPI: request sent), each including `₹{total:.2f}`. Tests: format a known order and assert the exact string; **round-trip** — write 2 orders to a `tmp_path` log, read back, split on `\n\n`, assert 2 blocks and that fields parse; assert append does not overwrite (write 1, write 1, expect 2).
- **Interface produced:** `format_order_record`, `log_order`, `payment_confirmation`, `PAYMENT_MODES`.
- **Acceptance:** format, round-trip, and append tests pass.
- **DoD:** commit, merge. **`core.py` is now feature-complete and fully tested.**

### S6 — Gradio shell + navigation skeleton (`app.py`)
- **Branch:** `feat/06-app-shell`
- **Objective:** Build the `gr.Blocks` wizard layout (6 steps), per-session state, the `@safe_handler` decorator, and forward navigation — with placeholder handlers that just advance (no validation yet).
- **Reasoning:** Establishing the navigation/state machine and the crash-safety wrapper *before* wiring logic isolates UI-structure bugs from validation bugs and gives S7 a working skeleton to attach behavior to.
- **Prerequisites:** S5 (core complete).
- **Reads:** STAGE2_PLAN §6 (architecture, gotchas), §9.2–§9.3 (defense in depth, step flow), §4 contracts.
- **Modifies:** `app.py`.
- **Tasks:** import `core`; load the three menus at module load inside try/except into module-level read-only constants (capture a `menu_error` string on failure — used by S7's banner). Build `gr.Blocks(show_error=True later at launch)`: a per-session `order = gr.State({})` and `session_ts = gr.State()`; six `gr.Group`s (intake, quantity, menu, bill, payment, confirm), only intake `visible=True`. Implement `show(active)` returning one `gr.update(visible=…)` per step. Implement `@safe_handler` (wraps a handler in `try/except Exception: raise gr.Error("Something went wrong — please retry.")`, re-raising `gr.Error` untouched). Wire `demo.load` to seed `session_ts` with an ISO timestamp. Placeholder "Next" handlers advance steps and thread `order`. `demo.launch(show_error=True, share=False)` under the main guard.
- **Interface produced:** `app.demo`, `show`, `safe_handler`, the six group handles, module-level loaded menus + `menu_error`.
- **Acceptance:** `python app.py` launches; clicking through advances all 6 steps and back to step 1 via a "New order" reset; `@safe_handler` verified by a temporary handler that raises a plain exception → shows the clean modal, app stays up. (Browser smoke check.)
- **DoD:** commit, merge.

### S7 — Wire logic into handlers + menu display + error banner
- **Branch:** `feat/07-wire-logic`
- **Objective:** Connect each step's handler to the `core` validators/pricing/logging so the full ordering flow works with real validation and re-prompts.
- **Reasoning:** With a tested core and a working shell, this session is pure integration — the highest-leverage, lowest-novelty step. Doing it in isolation keeps the diff reviewable.
- **Prerequisites:** S6.
- **Reads:** STAGE2_PLAN §2, §9.2–§9.3, §4 contracts; S6's `app.py`.
- **Modifies:** `app.py`.
- **Tasks:** Intake handler → `validate_name`/`validate_phone`; on fail `raise gr.Error(msg)` (stays on step); on success store into `order`, advance. Quantity handler → `validate_qty`. Menu step → render three numbered `gr.Markdown` lists from loaded menus (`f"{i}. {name} — ₹{price}"`); three textboxes; handler validates each via `validate_choice(raw, n)`, maps 1-based index → `Item`, calls `compute_bill`, stores `bill`, renders `render_bill_html` into the bill step's `gr.HTML`, advances. Payment handler → `validate_payment`; on success stamp `order["timestamp"]`, copy `session_start` from `session_ts`, `log_order(order)`, set the `payment_confirmation` message, advance to confirm. Confirm step shows summary + the confirmation message; "New order" resets state and visibility to intake. If `menu_error` is set, show an error banner at top and disable the "start" button. Keep all validation in the primary `.click()` handler (never `.success()`).
- **Interface produced:** the fully wired wizard.
- **Acceptance (browser):** happy path produces a correct bill and appends one block to `orders_log.txt`; each of the 8 edge cases shows the right `gr.Error` and stays on its step; menu-error banner appears when a menu file is renamed/removed.
- **DoD:** commit, merge.

### S8 — Integration, sample log, browser verification & packaging
- **Branch:** `feat/08-finalize`
- **Objective:** Final end-to-end verification, generate the sample `orders_log.txt`, finalize docs, and assemble the submission package.
- **Reasoning:** A dedicated closing session guarantees the deliverables exist and every rubric line is demonstrably satisfied, rather than assumed.
- **Prerequisites:** S7.
- **Reads:** STAGE2_PLAN §1 (rubric traceability), §9.6–§9.7; brief Stage 2 submission list.
- **Modifies:** `README.md`, `orders_log.txt` (generated), minor fixes only.
- **Tasks:** run `pytest -q` (all green). Launch `app.py`; place 2–3 varied orders (incl. one qty≥5 discount order and one qty<5) to generate a real `orders_log.txt`; verify blocks are blank-line separated and parse. Run the **full 8-edge-case browser pass** and record results. Re-test with a **swapped menu file** (different items/counts/prices) to confirm no hardcoding. Finalize `README.md` (run: `pip install -r requirements.txt` → `python app.py`; test: `pytest -q`; note Gradio pin + Python version). Confirm submission set present: `app.py`, `core.py`, the 3 `Types_of_*.txt`, `orders_log.txt` (+ `requirements.txt`, `test_core.py`). Tag the final commit.
- **Acceptance:** `pytest -q` green; all 8 edge cases pass live; swapped-file run works; `orders_log.txt` present and parseable; all deliverables in place.
- **DoD:** commit, merge, tag (e.g. `stage2-complete`).

---

## 6. Rubric coverage check (every session ties back to points)

| Rubric line (pts) | Covered by |
|---|---|
| Input validation & 8 edge cases (8) | S3 (logic + tests), S7 (UI re-prompts), S8 (live pass) |
| Menu file loading & swap-safety (6) | S2 (parser + fixtures), S7 (display + banner), S8 (swapped-file run) |
| Pricing & discount & GST (7) | S4 (engine + golden bill), S7 (bill render), S8 |
| Payment flow (4) | S5 (modes + confirmation), S7 (wiring), S8 |
| Order logging (5) | S5 (format + append + round-trip), S7 (write on completion), S8 (sample log) |

---

## 7. Appendix — golden values (use as fixed test oracles)

- **Golden bill:** Cheese Burst (B3, 229) + BBQ Chicken (P7, 379) + Extra Cheese (T2, 69) = **₹677/unit**; qty 5 → subtotal **3385.00** → discount **338.50** → post-discount **3046.50** → GST **548.37** → **total 3594.87**.
- **Discount boundary:** qty 4 → discount 0.00; qty 5 → 10%.
- **Provided menu counts:** 5 bases, 8 pizzas, 10 toppings.
- **Payment modes:** `1=Cash, 2=Card, 3=UPI`.
