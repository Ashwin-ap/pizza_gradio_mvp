# Spec — Session 1: Project setup & scaffold

## Kickoff prompt (paste into a NEW session)
> Read `mvp-design.md` in full (especially §1 Conventions, §4 Frozen contracts, and the `S1` block in §5),
> then read this spec file `.claude/specs/01-setup.md`. Implement **Session 1** to completion.
> Implement strictly to the frozen contracts — do not change any signature or data shape. Touch only the
> files listed under "Files". When done, run the verification command and confirm every Definition-of-Done
> item, then report results. Commit your work on the current branch `feat/01-setup`.

## Objective
Initialize the repo and create the empty module skeleton + tooling so later sessions have a runnable foundation.

## Why this session (reasoning)
A clean scaffold means every later session starts from `pytest` green (0 tests) and importable modules — no
environment debugging mid-feature. Git history from S1 onward also seeds the commit trail Stage 3 requires.

## Prerequisites
None. (Baseline is clean and committed on `main`.)

## Git note (already initialized)
The repo is already initialized and pushed to `origin` (`main` tracks `origin/main`) — do **not** run `git init`.
Work on the branch `feat/01-setup`; commit the scaffold and push.

## Branch
`feat/01-setup`  (base: `main`)

## Source references to read
- `mvp-design.md` → §1 conventions, §2 architecture & file layout, §4 frozen contracts, the `S1` block in §5
- `STAGE2_PLAN.md` → §7 (proposed module structure), §9.1 (separate pure logic from UI)
- Provided data files (confirm presence only): `Types_of_Base.txt`, `Types_of_Pizza.txt`, `Types_of_Toppings.txt`

## Frozen contracts relevant to this session
This session creates **stub signatures only** — every function body raises `NotImplementedError`.
Copy these signatures verbatim into `core.py` (from §4.2):

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

Data shapes referenced by the signatures (from §4.1) — include as a module-level comment/docstring for reference:

```python
# Item = {"id": str, "name": str, "price": float}
# Order = {session_start, name, phone, qty, base:Item, pizza:Item, topping:Item, bill:Bill, payment, timestamp}
# Bill  = {unit_price, quantity, subtotal, discount, post_discount, gst, total, discount_applied}
```

**Validator return convention:** `(ok, payload)` — on success `payload` is the cleaned/typed value; on failure
`payload` is the user-facing error string. (No need to implement here; just document the stubs accordingly.)

## Files
- **Create:**
  - `requirements.txt` — `gradio==5.49.1`, `pytest`
  - `.gitignore` — `__pycache__/`, `*.pyc`, `.venv/`, `flagged/`
  - `core.py` — module docstring + `class MenuError(Exception): pass` + all §4.2 signatures as stubs raising `NotImplementedError`
  - `app.py` — stub with `if __name__ == "__main__":` guard
  - `test_core.py` — imports `core`, one trivial `test_import` that passes
  - `README.md` — run/test instructions skeleton
- **Modify:** none.
- Do not create or modify any other files. (The 3 `Types_of_*.txt` already exist — confirm only, do not edit.)

## Implementation tasks
1. Create `requirements.txt` pinning `gradio==5.49.1` and `pytest` (exact Gradio pin — bare install pulls breaking 6.x).
2. Create `.gitignore` with `__pycache__/`, `*.pyc`, `.venv/`, `flagged/`.
3. Create `core.py`:
   - Module docstring describing the pure-logic role (no `gradio` import).
   - `class MenuError(Exception): pass`.
   - All function signatures from §4.2 as stubs whose bodies `raise NotImplementedError`.
   - Define `PAYMENT_MODES = {"1": "Cash", "2": "Card", "3": "UPI"}`.
   - Include the §4.1 data-shape comments for reference.
4. Create `app.py` as a stub: a module docstring noting it is the Gradio shell, and an
   `if __name__ == "__main__":` guard (may `pass` or print a placeholder — no Gradio wiring yet).
5. Create `test_core.py`: `import core` (and `import app` is optional) and a single `def test_import(): ...`
   that asserts the module imported (e.g. `assert core.MenuError`).
6. Create `README.md` skeleton: run instructions (`pip install -r requirements.txt` → `python app.py`),
   test instructions (`pytest -q`), and note the Gradio pin + Python 3.10–3.12.
7. Confirm the 3 `Types_of_*.txt` files exist (do not modify them).
8. Verify the environment: `pip install -r requirements.txt` resolves; `python -c "import core, app"` exits 0;
   `pytest -q` passes.

## Rules for implementation
- Implement to the §4 frozen contracts exactly; a contract change requires editing `mvp-design.md` first.
- `core.py` must not import `gradio` (pure logic).
- Money: `float` + `round(…, 2)`; never hardcode menu data. (No money logic this session — applies later.)
- Gradio pinned at `5.49.1`; Python 3.10–3.12.
- Conventional commits (`feat:`, `test:`, `chore:`); commit at working checkpoints.
- All stub bodies must `raise NotImplementedError` (except `MenuError` class and `PAYMENT_MODES` constant).

## Definition of done
- [ ] `pytest -q` is green (the single `test_import` passes).
- [ ] `python -c "import core, app"` exits 0.
- [ ] `pip install -r requirements.txt` resolves (gradio 5.49.1 + pytest).
- [ ] `git log` shows the scaffold commit.
- [ ] The 3 `Types_of_*.txt` files confirmed present.
- [ ] Verification command passes (see below).
- [ ] Work committed on `feat/01-setup`; ready to merge into `main`.

## Verification command
```
pip install -r requirements.txt
python -c "import core, app"
pytest -q
```
