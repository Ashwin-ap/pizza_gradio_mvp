# Spec — Session 3: Validators (`core.validate_*`)

## Kickoff prompt (paste into a NEW session)
> Read `mvp-design.md` in full (especially §1 Conventions, §4 Frozen contracts, and the `S3` block in §5),
> then read this spec file `.claude/specs/03-validators.md`. Implement **Session 3** to completion.
> Implement strictly to the frozen contracts — do not change any signature or data shape. Touch only the
> files listed under "Files". When done, run the verification command and confirm every Definition-of-Done
> item, then report results. Commit your work on the current branch `feat/03-validators`.

## Objective
Implement the five pure validators and a test that exercises all 8 mandated edge cases.

## Why this session (reasoning)
This is the 8-point line and the single biggest scoring risk. Pure functions let us prove every edge
case in `pytest` before any UI exists.

## Prerequisites
S1 (scaffold) — confirmed present on `main`: `core.py` exists with all five `validate_*` stubs raising
`NotImplementedError`, and `test_core.py` imports `core`. (S3 is independent of S2; ordered for cohesion.)

## Branch
`feat/03-validators`  (base: `main`)

## Source references to read
- `mvp-design.md` → §1 conventions, §4 frozen contracts, the `S3` block in §5
- `STAGE2_PLAN.md` → §2 (validation rules + exact error strings + the 8-case map)

## Frozen contracts relevant to this session

### Function signatures (§4.2 — frozen, do not change)
```python
def validate_name(raw: str)  -> tuple[bool, str]:        ...  # (True, clean) | (False, msg)
def validate_phone(raw: str) -> tuple[bool, str]:        ...  # (True, phone) | (False, msg)
def validate_qty(raw: str)   -> tuple[bool, "int|str"]:  ...  # (True, qty)   | (False, msg)
def validate_choice(raw: str, n: int) -> tuple[bool, "int|str"]: ...  # (True, 1..n) | (False, msg)
def validate_payment(raw: str) -> tuple[bool, str]:      ...  # (True, "Cash"/"Card"/"UPI") | (False, msg)
```

### Validator return convention (§4.2)
`(ok, payload)`. On **success** `payload` is the cleaned/typed value; on **failure** `payload` is the
user-facing error string. `app.py` does: `ok, val = validate_x(raw); if not ok: raise gr.Error(val)`.

### Already present on `main` (do not redefine)
`PAYMENT_MODES = {"1": "Cash", "2": "Card", "3": "UPI"}` is already declared at module level in `core.py`.
`validate_payment` should map a valid mode via this dict.

### Exact error strings (STAGE2_PLAN §2 — return these verbatim)
| Input | Rule | Error message |
|---|---|---|
| **Name** | letters + spaces only; 2–40 chars after strip; ≥1 letter | `Name must be 2–40 letters (spaces allowed), no numbers or symbols.` |
| **Phone** | exactly 10 digits; first ∈ {6,7,8,9} | `Phone must be exactly 10 digits and start with 6, 7, 8, or 9.` |
| **Quantity** | integer 1–10 | non-int → `Quantity must be a whole number between 1 and 10.` · >10 → `Maximum 10 pizzas per order.` |
| **Menu pick** | integer in `1..N` (position, not ID, not price) | `Enter the item NUMBER from the list (1–{N}).` |
| **Payment** | integer ∈ {1,2,3} | `Choose payment: 1 = Cash, 2 = Card, 3 = UPI.` |

> Note the en-dash `–` (U+2013) in the Name and Menu-pick messages and the `1 = Cash` spacing in Payment.
> Copy these strings character-for-character. For `validate_choice`, interpolate the actual `n`
> (e.g. `Enter the item NUMBER from the list (1–8).`).

## Files
- **Modify:** `core.py` (implement the five validators), `test_core.py` (add edge-case tests).
- Do not create or modify any other files.

## Implementation tasks
1. **`validate_name(raw)`** — `strip()`; reject empty/whitespace-only; allow letters + spaces only;
   length 2–40 after strip; require ≥1 letter. On success return `(True, cleaned_name)`. On any failure
   return `(False, "Name must be 2–40 letters (spaces allowed), no numbers or symbols.")`.
2. **`validate_phone(raw)`** — `strip()`; require exactly 10 characters, all digits; first digit ∈ {6,7,8,9}.
   On success `(True, phone)`; else `(False, "Phone must be exactly 10 digits and start with 6, 7, 8, or 9.")`.
3. **`validate_qty(raw)`** — `strip()`; reject empty; strict integer only via `re.fullmatch(r"\d+", s)`
   (must reject `"2.5"`, `"5.0"`, `"three"`, negative, empty — never truncate); parse `int`; range 1–10.
   - non-integer / 0 / empty → `(False, "Quantity must be a whole number between 1 and 10.")`
   - >10 → `(False, "Maximum 10 pizzas per order.")`
   - valid → `(True, qty_int)`
4. **`validate_choice(raw, n)`** — `strip()`; reject empty; digits-only via `re.fullmatch(r"\d+", s)`;
   parse `int`; must be in `1..n`. Rejects `0`, `>n`, a price like `229` (caught by the range check),
   letters, empty. On failure → `(False, f"Enter the item NUMBER from the list (1–{n}).")`.
   On success → `(True, choice_int)`.
5. **`validate_payment(raw)`** — `strip()`; accept only `"1"`/`"2"`/`"3"` (use `PAYMENT_MODES`);
   reject empty, `0`, `4`, non-int. On success `(True, "Cash"/"Card"/"UPI")`;
   else `(False, "Choose payment: 1 = Cash, 2 = Card, 3 = UPI.")`.
6. **Tests in `test_core.py`** — explicitly cover **all 8 mandated edge cases** and assert **both** the
   boolean and the message string:
   - #1 Name only spaces → `validate_name("   ")` rejects.
   - #2 Phone starting with 1 → `validate_phone("1234567890")` rejects (first-digit rule).
   - #3 Qty 0 and 11 → both reject (0 → whole-number msg; 11 → "Maximum 10 pizzas per order.").
   - #4 Choice 0 and >n → both reject.
   - #5 **Price entered as item number** (e.g. `validate_choice("229", 8)`) → rejects via range check.
   - #6 **Empty input at every field** → `validate_name("")`, `validate_phone("")`, `validate_qty("")`,
     `validate_choice("", 8)`, `validate_payment("")` all reject.
   - #7 **Non-integer qty** `validate_qty("three")` and `validate_qty("2.5")` → both reject (not truncated).
   - (#8 menu missing-price is the parser's job — covered in S2, not here.)
   - **Boundary tests:** qty `1` and qty `10` accept; choice `1` and choice `n` accept; phone valid
     (e.g. `"9876543210"`); name valid (e.g. `"Rajan Sharma"`); each payment `1`/`2`/`3` maps correctly.
   - Assert the cleaned/typed payload on success (e.g. `validate_qty("5") == (True, 5)`,
     `validate_payment("3") == (True, "UPI")`).

## Rules for implementation
- Implement to the §4 frozen contracts exactly; a contract change requires editing `mvp-design.md` first.
- `core.py` must not import `gradio` (pure logic). `re` is fine.
- Return the **exact** STAGE2_PLAN §2 error strings (mind the en-dashes `–`).
- Validators return `(ok, payload)` — never raise; the UI layer turns failures into `gr.Error`.
- Money / menu rules not relevant this session; do not hardcode any menu data.
- Python 3.10–3.12; Gradio not used here.
- Conventional commits (`feat:`, `test:`); commit at working checkpoints.

## Definition of done
- [ ] All 8 mandated edge-case tests pass (name-only-spaces; phone starting 1; qty 0 & 11; choice 0 & >n;
      price-as-item-number #5; empty at every field #6; non-integer qty "three"/"2.5" #7).
- [ ] Boundary tests pass (qty 1, qty 10; choice 1, choice n; valid name/phone; payments 1/2/3).
- [ ] Each test asserts **both** the boolean and the message/payload.
- [ ] No validator raises on bad input; all return `(ok, payload)`.
- [ ] `core.py` does not import `gradio`.
- [ ] Verification command passes (see below).
- [ ] Work committed on `feat/03-validators`; ready to merge into `main`.

## Verification command
```
pytest -q
```
