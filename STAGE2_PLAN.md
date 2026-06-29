# Stage 2 — Working MVP on Gradio · Planning & Research Notes

> **Status:** Planning only — no implementation yet.
> **Goal:** 30/30 on the Stage 2 rubric. Deliverables: `app.py` (or named `.py`) + 3 menu `.txt` files + a sample `orders_log.txt`.
> **Guiding principle:** correctness & robustness over aesthetics. *Must run end-to-end without crashing on any valid or invalid input.*

---

## 0. What we're building (one paragraph)

A Python **Gradio `gr.Blocks` wizard** that walks a customer through: customer intake → quantity → menu selection (base + pizza + topping) → itemised bill → payment → confirmation. Menu data is **loaded from three `.txt` files at runtime** (never hardcoded — the grader swaps them). The bill is rendered in **`gr.HTML`** (styled invoice, not a plain textbox). Every completed order is **appended to `orders_log.txt`** in a parseable, pipe-separated block format. Every input is validated defensively so the app never throws an unhandled exception.

---

## 1. Rubric → feature traceability (30 pts)

| Rubric line | Pts | What satisfies it |
|---|---|---|
| Input validation & error handling — all 8 edge cases, no unhandled exceptions | **8** | Strip → empty-check → strict typed-parse on every input; `gr.Error` re-prompts on the same step; try/except around all parsing & I/O |
| Menu file loading — 3 files at runtime, missing/malformed handled, survives file swap | **6** | Defensive `ID;Name;Price` parser; runtime load at startup; skip blank/malformed lines; numeric+positive price check; graceful error on missing file |
| Pricing & discount logic — threshold correct, GST on post-discount, accurate itemised bill | **7** | Fixed calc order (§4); 10% discount at qty ≥ 5; GST 18% on post-discount; itemised bill verified against the economics doc sample |
| Payment flow — 3 modes, invalid rejected, confirmation shown | **4** | Cash/Card/UPI only (1/2/3); reject 0/4/blank/non-int; per-mode confirmation message |
| Order logging — parseable, all fields, appended each run | **5** | `orders_log.txt` append mode, blank-line-delimited blocks, all 11+ fields |

---

## 2. Validation rules (the 8-point line — biggest risk)

Universal pattern for **every** input: **`.strip()` → empty-check → typed-parse inside try/except → range-check**. Never call `int("")`/`int("2.5")` unguarded.

| Input | Rule | Reject | Error message |
|---|---|---|---|
| **Name** | letters + spaces only; 2–40 chars after strip; ≥1 letter | empty/whitespace; <2 or >40; any digit/symbol | "Name must be 2–40 letters (spaces allowed), no numbers or symbols." |
| **Phone** | exactly 10 digits; first ∈ {6,7,8,9} | empty; len≠10; non-digit; starts 0–5 | "Phone must be exactly 10 digits and start with 6, 7, 8, or 9." |
| **Quantity** | integer 1–10 | empty; "three"/"2.5"/"5.0"; 0; negative; >10 | non-int → "Quantity must be a whole number between 1 and 10." · >10 → "Maximum 10 pizzas per order." |
| **Menu pick** (base/pizza/topping) | integer in `1..N` (position number, not ID, not price) | empty; 0; >N; non-digit; a price value | "Enter the item NUMBER from the list (1–{N})." |
| **Payment** | integer ∈ {1,2,3} | empty; 0; 4; non-int | "Choose payment: 1 = Cash, 2 = Card, 3 = UPI." |

### 8 mandated edge cases → handler
1. Name only spaces → name validator (strip→len 0)
2. 10 digits starting with 1 → phone first-digit rule
3. Qty 0 and 11 → quantity range
4. Item selection 0 or > menu length → menu range `1..N`
5. **Price entered instead of item number** → caught only by the range check (e.g. 229 > N) — easy to miss
6. Empty input at every prompt → each field's empty-check before parse
7. **Non-integer qty ("three", "2.5")** → strict int parse must reject, not truncate
8. Menu file with missing price → parser skips the line / fails gracefully

> Cases **#5** and **#7** are the most commonly missed. Test both explicitly.

---

## 3. Defensive menu parsing (`ID;Name;Price`)

Per line: read UTF-8 → `strip()` → skip blanks → `split(";")`.
- `len(parts) < 3` → malformed, skip.
- `len(parts) > 3` (extra semicolons) → `id=parts[0]`, `price=parts[-1]`, `name=";".join(parts[1:-1])`.
- Empty id or name → skip.
- `float(price)` in try/except; non-numeric → skip; `price <= 0` → skip (negatives are malformed).

File-level:
- **Missing file** (`FileNotFoundError`) → clear banner ("Menu file 'X' not found"), disable order flow, **no traceback**.
- **0 valid items after parse** → treat as fatal for that category, clear message, graceful stop.
- Wrap startup load in try/except; render a single error banner instead of crashing the process.

Fixtures to test: trailing newline; blank middle line; `B6;Stuffed;` (no price); `B7;;199` (no name); `B8;Weird;Name;199` (extra `;`); `B9;Bad;abc` (non-numeric); `B10;Neg;-50` (negative); fully empty file; spaces around every field.

> Note: the **shipped files differ from the brief's example table** (topping is `Button Mushrooms` not `Mushrooms`; 8 pizzas; toppings ₹39–69). This confirms: **never hardcode menu items.** Map by file content/ID only.

---

## 4. Pricing engine (exact order)

```
unit_price    = base_price + pizza_price + topping_price
subtotal      = unit_price * quantity
discount      = round(subtotal * 0.10, 2)  if quantity >= 5  else 0.00
post_discount = subtotal - discount
gst           = round(post_discount * 0.18, 2)     # GST on POST-discount
final_total   = round(post_discount + gst, 2)
```

Round at discount / GST / final steps to 2 decimals. (Optionally use `decimal.Decimal` + `ROUND_HALF_UP` for currency-grade exactness — acceptable either way if consistent.)

### Golden test (from economics doc §7 — verified ✓)
Cheese Burst (base, ₹229) + BBQ Chicken (pizza, ₹379) + Extra Cheese (topping, ₹69) = **₹677/unit**; qty 5 → subtotal **₹3385** → 10% discount **₹338.50** → post-discount **₹3046.50** → GST 18% **₹548.37** → **total ₹3594.87**. Math confirmed exact. Use this as a unit test.

> ⚠️ GST is **18%**, on the **post-discount** total. (The Gradio research snippet mistakenly showed "5%" — ignore that.)

---

## 5. Order log format (`orders_log.txt`)

One block per order; pipe-separated `key=value` fields on lines; **blank line between orders**; append mode; UTF-8; create if absent.

```
timestamp=2026-06-29T14:32:05 | name=Rajan Sharma | phone=9876543210 | base=B3:Cheese Burst:229 | pizza=P7:BBQ Chicken:379 | topping=T2:Extra Cheese:69 | unit_price=677 | quantity=5 | subtotal=3385.00 | discount=338.50 | gst=548.37 | total=3594.87 | payment=UPI

timestamp=2026-06-29T14:40:11 | name=Asha Verma | phone=8123456780 | base=B1:Thin Crust:149 | pizza=P1:Margherita:299 | topping=T4:Green Peppers:39 | unit_price=487 | quantity=2 | subtotal=974.00 | discount=0.00 | gst=175.32 | total=1149.32 | payment=Cash
```

Each item field carries `ID:Name:Price` so the log stays self-contained after a file swap. Names are letters+spaces only, so `|`/`;`/`:` collisions can't occur. Also log a **session-start timestamp** when a new session begins (brief requirement). Wrap writes in a `threading.Lock` (handlers run concurrently) + try/except.

---

## 6. Gradio architecture

**Decision: `gr.Blocks` wizard, not chatbot.** A chat interface adds an NL-parsing failure mode with no upside here. **Use `gr.Textbox` for every input — never `gr.Number`** (see trap below): raw strings reach our validators so *we* control all parsing and rejection.

> ⚠️ **`gr.Number` coercion trap (verified):** `gr.Number(precision=0)` silently rounds `2.5`→`2` *before* the handler runs, and plain `gr.Number` hands you a `float`. Either way the handler never sees the literal `"2.5"`/`"three"` and **cannot reject it** — which would fail edge case #7. `gr.Textbox` hands the handler the raw `str`, so we parse with a strict `re.fullmatch(r"\d+", s)` and reject anything non-integer ourselves.

**Step flow:** each step is a `gr.Group`; all groups exist in the layout, only one `visible=True` at a time. A per-session **`gr.State`** dict carries the accumulating order. Each "Next" button handler returns one `gr.update(visible=...)` per group + the updated state.

```python
import gradio as gr
STEPS = ["intake", "quantity", "menu", "bill", "payment", "confirm"]

def show(active):
    return [gr.update(visible=(s == active)) for s in STEPS]

with gr.Blocks() as demo:
    order = gr.State({})            # per-session — NOT a module global
    # one gr.Group per step ... groups = [g_intake, g_quantity, ...]
    def go_quantity(name, phone, order):
        if not name.strip():
            raise gr.Error("Name must be 2–40 letters.")   # stays on step
        order = {**order, "name": name.strip(), "phone": phone.strip()}
        return [order, *show("quantity")]
    b1.click(go_quantity, [name, phone, order], [order, *groups])
```

**Critical gotchas:**
- **`gr.State` is per-session** (per browser) — safe for concurrent users. **Module-level globals are SHARED across all users** → never store per-user order data in a global. Globals are fine only for read-only constants (menu, GST rate).
- **Validation UX:** `raise gr.Error("msg")` shows a red toast and **aborts the handler without returning outputs** → user stays on the same step automatically. This is the cleanest "re-prompt without crashing" pattern. Wrap all risky logic so a stack trace never reaches the grader. Use inline `gr.Markdown` only for persistent soft hints.
- **Bill rendering:** use **`gr.HTML`** for the itemised invoice — full control over aligned columns, ₹ symbol, and bolded Subtotal/Discount/GST/**Total** footer. (`gr.Dataframe` is fine for the line-items grid but awkward for styled summary rows. Either satisfies "not a plain textbox.")
- **File I/O:** read menu files once at startup (read-only shared state = safe). Guard log appends with a `threading.Lock` + try/except (handlers run in a ~40-thread pool).
- **Launch:** `demo.launch()` → local server on `127.0.0.1:7860`. Keep `share=False` for a reliable local grading demo.

**Version pinning (verified):** pin **`gradio==5.49.1`** in `requirements.txt`. A bare `pip install gradio` now pulls **6.x** (current stable 6.19.0), which has breaking changes — so pin explicitly. Requires Python ≥ 3.10 (use 3.10–3.12). The patterns above (`gr.State`, `gr.update`, `gr.Error`, `demo.load`, visible-group toggling, `.click()`) are stable across Gradio 4/5/6.

**Launch flags:** `demo.launch(show_error=True)` — the default has varied by version; setting it explicitly guarantees our `gr.Error` messages render in the browser modal rather than only the terminal.

---

## 7. Proposed module structure (single `.py` is fine for submission)

- `load_menu(path)` → defensive parser returning ordered list of `{id,name,price}`; raises a typed error caught at startup.
- `validate_name`, `validate_phone`, `validate_qty`, `validate_choice`, `validate_payment` → pure functions returning `(ok, value_or_errormsg)`; unit-testable without Gradio.
- `compute_bill(base, pizza, topping, qty)` → dict with all line items + totals (the §4 engine).
- `render_bill_html(bill)` → styled invoice string.
- `log_order(order)` → lock-guarded append to `orders_log.txt`.
- Gradio `gr.Blocks` UI wiring at the bottom; `if __name__ == "__main__": demo.launch()`.

Keeping validation/pricing/parsing as **pure functions** lets us write a tiny test harness covering all 8 edge cases + the golden bill without launching the UI — strong insurance for the 8-point validation line.

---

## 8. Locked decisions (confirmed)

1. **Toppings:** **exactly one** topping per pizza (one base + one pizza + one topping). Matches the economics doc sample bill; keeps bill math and log format simple.
2. **Menu selection input:** **`gr.Textbox`** (selection by item number), parsed manually — **never `gr.Number`** (see the §6 coercion trap). Matches the spec wording literally and lets us demonstrate range / non-integer / out-of-range rejection directly (covers edge cases #4 and #5 explicitly). Applies to all numeric inputs (quantity, base/pizza/topping#, payment), not just menu selection. Display each list as a numbered list with names + ₹ prices alongside the input.
3. **Money:** **`float` + `round(…, 2)`** at the discount/GST/final steps. Matches the verified golden bill exactly; simplest for the MVP.

---

## 9. Definitive build approach (verified)

### 9.1 Guiding principle — separate pure logic from the UI
All parsing, validation, pricing, and log formatting live as **pure functions** with no Gradio import. The Gradio layer is a thin shell that calls them. Payoffs: (a) the entire 8-point validation surface + golden bill are unit-testable without a browser; (b) bugs are isolated; (c) Stage 3's "modify a live feature" port becomes trivial.

### 9.2 The "no unhandled exception" guarantee — defense in depth (3 layers)
1. **`gr.Textbox` for every input** → raw `str` reaches our code; no widget-level coercion can mask bad input (the `gr.Number` trap).
2. **Explicit validators** raise `gr.Error("specific message")` for every *expected* bad input. Raising suppresses all outputs → the user stays on the same step and re-prompts. *Keep validation in the primary `.click()` handler, never a chained `.success()`* (a known bug can hang outputs there).
3. **`@safe_handler` decorator** wraps each handler body in `try/except Exception` and re-raises as `gr.Error("Something went wrong — please retry.")`. Even an unforeseen bug becomes a clean modal, never a traceback. Combined with `launch(show_error=True)`, nothing ugly ever reaches the grader.

### 9.3 Step flow (forward-only + restart)
Six `gr.Group`s, one visible at a time; a single per-session `gr.State` order dict threads through every handler.

| Step | Inputs (all Textbox) | Validates | On success |
|---|---|---|---|
| 1 Intake | name, phone | §2 name + phone rules | advance; session-start timestamp already in state |
| 2 Quantity | qty | int 1–10, strict | store qty + discount eligibility |
| 3 Menu | base#, pizza#, topping# (3 numbered `gr.Markdown` lists alongside) | each `1..N` (N from loaded file) | compute bill |
| 4 Bill | — | — | render `gr.HTML` invoice; "Confirm" → payment |
| 5 Payment | mode (1/2/3) | ∈ {1,2,3} | per-mode confirmation message; **write order to `orders_log.txt` here** (order is now complete) |
| 6 Confirm | — | — | show success + summary; "New order" resets state to step 1 |

No back-navigation (avoids state-restoration bug surface). "New order" is the only reset.

**Session-start timestamp:** `demo.load(lambda: <now>, outputs=session_ts_state)` fires once per page-load/session and seeds the timestamp; the order record's `timestamp` is stamped at write time (step 5).

### 9.4 Menu loading at startup (no hard exit)
Load all three files once at module load inside try/except. On any failure, **don't `sys.exit`** — launch the app showing an error banner with the disabled order flow, so the grader sees the clear message in the UI (satisfies "display a clear error and exit gracefully" without looking like a crash). `N` for each list is computed from the parsed result, so a swapped file of any size just works.

### 9.5 Concurrency
`threading.Lock` around the log append regardless of queue settings (sync handlers run in a threadpool). `.queue()` not required for a local demo.

### 9.6 Build sequencing (when we implement)
1. **Pure core + test harness** (`test_core.py`): parser, validators, pricing, log writer. Assert all 8 edge cases, the golden bill (₹3594.87), discount boundary (qty 4 → ₹0, qty 5 → 10%), and the parser fixtures from §3. Green before any UI.
2. **Gradio shell**: wizard groups, `gr.State`, `@safe_handler`, `gr.Error` validation wiring, `demo.load` session stamp.
3. **Bill HTML** renderer (§6).
4. **Generate sample `orders_log.txt`** by placing 2–3 orders through the running app.
5. **Manual edge-case pass** in the browser, then package.

### 9.7 Submission package
- `app.py` (single file is fine) · the 3 menu `.txt` files · sample `orders_log.txt` *(the 3 required deliverables)*
- `requirements.txt` (`gradio==5.49.1`) and optionally `test_core.py` + a short `README.md` — not required, but demonstrate rigor.
```
