# Spec — Session 4: Pricing engine + bill HTML (`core.compute_bill`, `core.render_bill_html`)

## Kickoff prompt (paste into a NEW session)
> Read `mvp-design.md` in full (especially §1 Conventions, §4 Frozen contracts, and the `S4` block in §5),
> then read this spec file `.claude/specs/04-pricing.md`. Implement **Session 4** to completion.
> Implement strictly to the frozen contracts — do not change any signature or data shape. Touch only the
> files listed under "Files". When done, run the verification command and confirm every Definition-of-Done
> item, then report results. Commit your work on the current branch `feat/04-pricing`.

## Objective
Implement the pricing calculation and the HTML invoice renderer, verified against the golden bill.

## Why this session (reasoning)
7 rubric points; correctness is checkable exactly against the economics-doc sample. Bundling the (pure,
string-returning) HTML renderer here keeps the UI session light and lets us assert invoice contents without
a browser.

## Prerequisites
S2 (uses `Item` shape) — confirmed present on `main` (`load_menu` implemented).

## Branch
`feat/04-pricing`  (base: `main`)

## Source references to read
- `mvp-design.md` → §1 conventions, §4 frozen contracts, the `S4` block in §5, §7 appendix golden values
- `STAGE2_PLAN.md` → §4 (calc order + golden bill), §6 (bill rendering)
- `SliceMatic_Business_Economics.md` §7 (golden bill source), if present

## Frozen contracts relevant to this session

### Data shapes (§4.1)
```python
# A menu item (output of load_menu) — consumed by compute_bill
Item = {"id": str, "name": str, "price": float}

# Bill = output of compute_bill
Bill = {
    "unit_price": float, "quantity": int,
    "subtotal": float, "discount": float, "post_discount": float,
    "gst": float, "total": float, "discount_applied": bool,
}
```

### Function signatures (§4.2 — frozen, do not change)
```python
def compute_bill(base: Item, pizza: Item, topping: Item, qty: int) -> Bill: ...
def render_bill_html(bill: Bill, name: str) -> str: ...   # styled invoice (STAGE2_PLAN §6)
```

### Pricing engine — exact calc order (STAGE2_PLAN §4)
```
unit_price    = base_price + pizza_price + topping_price
subtotal      = unit_price * quantity
discount      = round(subtotal * 0.10, 2)  if quantity >= 5  else 0.00
post_discount = subtotal - discount
gst           = round(post_discount * 0.18, 2)     # GST on POST-discount
total         = round(post_discount + gst, 2)
discount_applied = quantity >= 5
```
GST is **18%**, applied to the **post-discount** total. Round at discount / GST / total steps to 2 decimals.

## Files
- **Create:** none
- **Modify:** `core.py` (implement `compute_bill`, `render_bill_html` — currently stubs), `test_core.py` (add pricing + render tests)
- Do not create or modify any other files.

## Implementation tasks
1. Implement `compute_bill(base, pizza, topping, qty)`:
   - [ ] `unit_price = base["price"] + pizza["price"] + topping["price"]`
   - [ ] `subtotal = unit_price * qty`
   - [ ] `discount = round(subtotal * 0.10, 2)` if `qty >= 5` else `0.00`
   - [ ] `post_discount = subtotal - discount`
   - [ ] `gst = round(post_discount * 0.18, 2)`
   - [ ] `total = round(post_discount + gst, 2)`
   - [ ] set `discount_applied = qty >= 5`
   - [ ] return a `Bill` dict with all eight keys.
2. Implement `render_bill_html(bill, name)`:
   - [ ] Return a `<table>`-based styled invoice string (HTML), not a plain textbox dump.
   - [ ] Use the `₹` symbol; right-align amount columns.
   - [ ] Show line items derived from the bill (unit price, quantity, subtotal).
   - [ ] Footer block with **Subtotal / Discount / GST 18% / Total** (Total bold).
   - [ ] Include the customer `name` in the invoice.
   - [ ] Format money with 2 decimals (e.g. `₹3594.87`).
3. Add tests to `test_core.py`:
   - [ ] **Golden bill:** Cheese Burst (229) + BBQ Chicken (379) + Extra Cheese (69), qty 5 → `subtotal 3385.00`, `discount 338.50`, `post_discount 3046.50`, `gst 548.37`, `total 3594.87`, `discount_applied True`.
   - [ ] **Discount boundary:** qty 4 → `discount 0.00`, `discount_applied False`; qty 5 → 10% discount applied.
   - [ ] A no-discount case (qty < 5) computes correctly.
   - [ ] `render_bill_html` output contains `₹3594.87`, `Subtotal`, `Discount`, `GST`, `Total`.

## Rules for implementation
- Implement to the §4 frozen contracts exactly; a contract change requires editing `mvp-design.md` first.
- `core.py` must not import `gradio` (pure logic).
- Money: `float` + `round(…, 2)`; never hardcode menu data — construct test `Item`s inline in the test, not in `core.py`.
- Gradio pinned at `5.49.1`; Python 3.10–3.12.
- Conventional commits (`feat:`, `test:`, `chore:`); commit at working checkpoints.
- Build `Item`s for tests as literal dicts matching the frozen `Item` shape; do not read menu files for the golden-bill assertions.

## Definition of done
- [ ] `compute_bill` returns the golden bill exactly (total `3594.87`, gst `548.37`, discount `338.50`).
- [ ] Discount boundary correct (qty 4 → 0.00; qty 5 → 10%) and `discount_applied` set accordingly.
- [ ] `render_bill_html` output contains `₹3594.87`, `Subtotal`, `Discount`, `GST`, `Total`.
- [ ] Verification command passes (see below).
- [ ] Work committed on `feat/04-pricing`; ready to merge into `main`.

## Verification command
```
pytest -q
```
