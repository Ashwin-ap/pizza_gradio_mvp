# Spec — Session 2: Menu parser (`core.load_menu`)

## Kickoff prompt (paste into a NEW session)
> Read `mvp-design.md` in full (especially §1 Conventions, §4 Frozen contracts, and the `S2` block in §5),
> then read this spec file `.claude/specs/02-menu-parser.md`. Implement **Session 2** to completion.
> Implement strictly to the frozen contracts — do not change any signature or data shape. Touch only the
> files listed under "Files". When done, run the verification command and confirm every Definition-of-Done
> item, then report results. Commit your work on the current branch `feat/02-menu-parser`.

## Objective
Implement the defensive `ID;Name;Price` parser and its full fixture test suite.

## Why this session (reasoning)
Menu loading is 6 rubric points and the grader swaps the files — robustness here is non-negotiable. Building it first gives later sessions real `Item` data to price and display.

## Prerequisites
S1 (Project setup & scaffold) — confirmed present on `main` (the `core.py` stub with `class MenuError(Exception)` and `def load_menu(path) -> list` raising `NotImplementedError`, plus `test_core.py` with a passing `test_import`, are merged into `main`).

## Branch
`feat/02-menu-parser`  (base: `main`)

## Source references to read
- `mvp-design.md` → §1 conventions, §4 frozen contracts, the `S2` block in §5
- `STAGE2_PLAN.md` → §3 (defensive menu parsing rules + fixtures), §8.2 (selection-by-number note)
- Provided data files this session validates against: `Types_of_Base.txt`, `Types_of_Pizza.txt`, `Types_of_Toppings.txt`

## Frozen contracts relevant to this session

### Data shape (output element)
```python
# A menu item (output of load_menu)
Item = {"id": str, "name": str, "price": float}
```

### Function signatures (frozen — implement exactly)
```python
class MenuError(Exception): ...                      # missing file / zero valid items

def load_menu(path: str) -> list[Item]: ...
    # Defensive parse of "ID;Name;Price" per STAGE2_PLAN §3.
    # Skips blank/malformed/non-numeric/non-positive lines.
    # Raises MenuError if the file is missing OR yields zero valid items.
```

`load_menu` returns an **ordered** `list[Item]` preserving file order. Position in this list is the
1-based "item number" later sessions use for selection — order must be stable.

## Files
- **Create:** none.
- **Modify:** `core.py` (implement `load_menu`; keep/confirm `MenuError`), `test_core.py` (add parser tests).
- Do not create or modify any other files. (Fixture files must be written to a pytest `tmp_path`, **not** committed to the repo.)

## Implementation tasks
Per STAGE2_PLAN §3, implement `load_menu(path)` with this exact per-line logic:
1. Open the file as **UTF-8**. If the file does not exist (`FileNotFoundError`), raise `MenuError` with a clear message (e.g. `f"Menu file '{path}' not found"`).
2. For each line: `strip()`; skip if blank.
3. `split(";")` on the stripped line.
4. If `len(parts) < 3` → malformed, **skip**.
5. If `len(parts) > 3` (extra semicolons) → `id = parts[0]`, `price = parts[-1]`, `name = ";".join(parts[1:-1])`.
6. Otherwise (`len == 3`) → `id, name, price = parts`.
7. `strip()` `id`, `name`, and the price string. If `id` is empty **or** `name` is empty → **skip**.
8. Parse price: `float(price_str)` inside a `try/except (ValueError)`; on non-numeric → **skip**.
9. If `price <= 0` → **skip** (negatives/zero are malformed).
10. Append `{"id": id, "name": name, "price": float(price)}` to the result list, preserving order.
11. After parsing, if the result list is **empty** (zero valid items) → raise `MenuError` (clear message).

Add parser tests to `test_core.py` (use pytest `tmp_path` to write fixture files; do not commit fixtures):
- Trailing newline at end of file → still parses correctly.
- Blank middle line → skipped, surrounding lines parse.
- `B6;Stuffed;` (no price) → skipped.
- `B7;;199` (empty name) → skipped.
- `B8;Weird;Name;199` (extra `;`) → parses with `name == "Weird;Name"`, `id == "B8"`, `price == 199.0`.
- `B9;Bad;abc` (non-numeric price) → skipped.
- `B10;Neg;-50` (negative price) → skipped.
- Spaces around fields (e.g. ` B1 ; Thin Crust ; 149 `) → trimmed and parsed.
- Fully empty file → raises `MenuError`.
- Missing/nonexistent file path → raises `MenuError`.
- **Provided-file counts:** `load_menu("Types_of_Base.txt")` → 5 items; `Types_of_Pizza.txt` → 8 items; `Types_of_Toppings.txt` → 10 items. (Optionally assert a known item, e.g. B3 = Cheese Burst @ 229.0.)

## Rules for implementation
- Implement to the §4 frozen contracts exactly; a contract change requires editing `mvp-design.md` first.
- `core.py` must **not** import `gradio` (pure logic).
- Money is `float`; never hardcode menu data — all items come from parsing the file.
- Gradio pinned at `5.49.1`; Python 3.10–3.12.
- Conventional commits (`feat:`, `test:`, `chore:`); commit at working checkpoints.
- `load_menu` must never let an unhandled exception escape for a missing file or a file of all-malformed lines — both surface as `MenuError`.
- Result order must match file order (selection-by-number depends on it).
- Do not commit generated fixture files; use `tmp_path`.

## Definition of done
- [ ] `load_menu` implemented per §3 rules; `MenuError` raised on missing file and on zero valid items.
- [ ] All parser fixture tests pass (trailing newline, blank line, no-price, no-name, extra-`;`, non-numeric, negative, spaces, empty file, missing file).
- [ ] Provided-file count tests pass: 5 bases, 8 pizzas, 10 toppings.
- [ ] `core.py` imports without `gradio`; `python -c "import core"` exits 0.
- [ ] Verification command passes (see below).
- [ ] Work committed on `feat/02-menu-parser`; ready to merge into `main`.

## Verification command
```
pytest -q
```
