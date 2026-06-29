"""
core.py — Pure business logic for SliceMatic.

No gradio import. All testable logic (menu parsing, validation, pricing,
bill rendering, order persistence) lives here as pure functions.

Data shapes (from mvp-design.md §4.1):
    Item  = {"id": str, "name": str, "price": float}
    Order = {
        "session_start": str,   # ISO-8601
        "name": str,
        "phone": str,
        "qty": int,
        "base": Item, "pizza": Item, "topping": Item,
        "bill": Bill,
        "payment": str,         # "Cash" | "Card" | "UPI"
        "timestamp": str,       # ISO-8601
    }
    Bill  = {
        "unit_price": float, "quantity": int,
        "subtotal": float, "discount": float, "post_discount": float,
        "gst": float, "total": float, "discount_applied": bool,
    }

Validator return convention: (ok, payload)
    On success: payload is the cleaned/typed value.
    On failure: payload is the user-facing error string.
    app.py does: ok, val = validate_x(raw); if not ok: raise gr.Error(val)
"""


import re

class MenuError(Exception):
    """Raised when a menu file is missing or yields zero valid items."""
    pass


PAYMENT_MODES = {"1": "Cash", "2": "Card", "3": "UPI"}


def load_menu(path: str) -> list:
    """Defensive parse of 'ID;Name;Price' lines.

    Skips blank/malformed/non-numeric/non-positive lines.
    Raises MenuError if the file is missing OR yields zero valid items.
    Returns list[Item].
    """
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise MenuError(f"Menu file '{path}' not found")

    items = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split(";")
        if len(parts) < 3:
            continue
        if len(parts) > 3:
            id_ = parts[0]
            price_str = parts[-1]
            name = ";".join(parts[1:-1])
        else:
            id_, name, price_str = parts
        id_ = id_.strip()
        name = name.strip()
        price_str = price_str.strip()
        if not id_ or not name:
            continue
        try:
            price = float(price_str)
        except ValueError:
            continue
        if price <= 0:
            continue
        items.append({"id": id_, "name": name, "price": price})

    if not items:
        raise MenuError(f"Menu file '{path}' contains no valid items")

    return items


def validate_name(raw: str) -> tuple:
    """(True, clean_name) | (False, error_msg)"""
    _NAME_ERR = "Name must be 2–40 letters (spaces allowed), no numbers or symbols."
    s = raw.strip()
    if not s:
        return (False, _NAME_ERR)
    if not re.fullmatch(r"[A-Za-z ]+", s):
        return (False, _NAME_ERR)
    if len(s) < 2 or len(s) > 40:
        return (False, _NAME_ERR)
    if not any(c.isalpha() for c in s):
        return (False, _NAME_ERR)
    return (True, s)


def validate_phone(raw: str) -> tuple:
    """(True, phone) | (False, error_msg)"""
    _PHONE_ERR = "Phone must be exactly 10 digits and start with 6, 7, 8, or 9."
    s = raw.strip()
    if len(s) != 10 or not s.isdigit():
        return (False, _PHONE_ERR)
    if s[0] not in "6789":
        return (False, _PHONE_ERR)
    return (True, s)


def validate_qty(raw: str) -> tuple:
    """(True, qty:int) | (False, error_msg)"""
    _QTY_ERR = "Quantity must be a whole number between 1 and 10."
    _QTY_MAX_ERR = "Maximum 10 pizzas per order."
    s = raw.strip()
    if not s or not re.fullmatch(r"\d+", s):
        return (False, _QTY_ERR)
    qty = int(s)
    if qty == 0:
        return (False, _QTY_ERR)
    if qty > 10:
        return (False, _QTY_MAX_ERR)
    return (True, qty)


def validate_choice(raw: str, n: int) -> tuple:
    """(True, choice:int 1..n) | (False, error_msg)"""
    _CHOICE_ERR = f"Enter the item NUMBER from the list (1–{n})."
    s = raw.strip()
    if not s or not re.fullmatch(r"\d+", s):
        return (False, _CHOICE_ERR)
    choice = int(s)
    if choice < 1 or choice > n:
        return (False, _CHOICE_ERR)
    return (True, choice)


def validate_payment(raw: str) -> tuple:
    """(True, 'Cash'|'Card'|'UPI') | (False, error_msg)"""
    _PAYMENT_ERR = "Choose payment: 1 = Cash, 2 = Card, 3 = UPI."
    s = raw.strip()
    if s not in PAYMENT_MODES:
        return (False, _PAYMENT_ERR)
    return (True, PAYMENT_MODES[s])


def compute_bill(base: dict, pizza: dict, topping: dict, qty: int) -> dict:
    """Compute the Bill dict for the given items and quantity."""
    unit_price = base["price"] + pizza["price"] + topping["price"]
    subtotal = unit_price * qty
    discount = round(subtotal * 0.10, 2) if qty >= 5 else 0.00
    post_discount = subtotal - discount
    gst = round(post_discount * 0.18, 2)
    total = round(post_discount + gst, 2)
    return {
        "unit_price": unit_price,
        "quantity": qty,
        "subtotal": subtotal,
        "discount": discount,
        "post_discount": post_discount,
        "gst": gst,
        "total": total,
        "discount_applied": qty >= 5,
    }


def render_bill_html(bill: dict, name: str) -> str:
    """Return a styled HTML invoice string (table with ₹ amounts)."""
    discount_row = (
        f'<tr><td>Discount (10%)</td><td style="text-align:right">₹{bill["discount"]:.2f}</td></tr>'
        if bill["discount_applied"]
        else f'<tr><td>Discount</td><td style="text-align:right">₹0.00</td></tr>'
    )
    return f"""<table style="border-collapse:collapse;width:100%;font-family:sans-serif">
  <tr style="background:#d32f2f;color:white">
    <th colspan="2" style="padding:10px;text-align:center">SliceMatic — Invoice</th>
  </tr>
  <tr><td style="padding:6px">Customer</td><td style="text-align:right;padding:6px">{name}</td></tr>
  <tr style="background:#f5f5f5"><td style="padding:6px">Unit Price</td><td style="text-align:right;padding:6px">₹{bill["unit_price"]:.2f}</td></tr>
  <tr><td style="padding:6px">Quantity</td><td style="text-align:right;padding:6px">{bill["quantity"]}</td></tr>
  <tr style="background:#f5f5f5"><td style="padding:6px">Subtotal</td><td style="text-align:right;padding:6px">₹{bill["subtotal"]:.2f}</td></tr>
  {discount_row}
  <tr style="background:#f5f5f5"><td style="padding:6px">GST 18%</td><td style="text-align:right;padding:6px">₹{bill["gst"]:.2f}</td></tr>
  <tr style="border-top:2px solid #333"><td style="padding:8px"><strong>Total</strong></td><td style="text-align:right;padding:8px"><strong>₹{bill["total"]:.2f}</strong></td></tr>
</table>"""


def format_order_record(order: dict) -> str:
    """Return a single pipe-separated line for the orders log (no trailing blank)."""
    raise NotImplementedError


def log_order(order: dict, path: str = "orders_log.txt") -> None:
    """Lock-guarded append of the order record + blank-line separator."""
    raise NotImplementedError


def payment_confirmation(mode: str, total: float) -> str:
    """Return the per-mode payment confirmation message including ₹total."""
    raise NotImplementedError
