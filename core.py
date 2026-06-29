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
    raise NotImplementedError


def validate_phone(raw: str) -> tuple:
    """(True, phone) | (False, error_msg)"""
    raise NotImplementedError


def validate_qty(raw: str) -> tuple:
    """(True, qty:int) | (False, error_msg)"""
    raise NotImplementedError


def validate_choice(raw: str, n: int) -> tuple:
    """(True, choice:int 1..n) | (False, error_msg)"""
    raise NotImplementedError


def validate_payment(raw: str) -> tuple:
    """(True, 'Cash'|'Card'|'UPI') | (False, error_msg)"""
    raise NotImplementedError


def compute_bill(base: dict, pizza: dict, topping: dict, qty: int) -> dict:
    """Compute the Bill dict for the given items and quantity."""
    raise NotImplementedError


def render_bill_html(bill: dict, name: str) -> str:
    """Return a styled HTML invoice string (table with ₹ amounts)."""
    raise NotImplementedError


def format_order_record(order: dict) -> str:
    """Return a single pipe-separated line for the orders log (no trailing blank)."""
    raise NotImplementedError


def log_order(order: dict, path: str = "orders_log.txt") -> None:
    """Lock-guarded append of the order record + blank-line separator."""
    raise NotImplementedError


def payment_confirmation(mode: str, total: float) -> str:
    """Return the per-mode payment confirmation message including ₹total."""
    raise NotImplementedError
