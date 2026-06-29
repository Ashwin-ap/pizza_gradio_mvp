import os
import pytest
import core
from core import (
    load_menu, MenuError,
    validate_name, validate_phone, validate_qty, validate_choice, validate_payment,
    compute_bill, render_bill_html,
)


def test_import():
    assert core.MenuError


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def write_menu(tmp_path, filename, content):
    p = tmp_path / filename
    p.write_text(content, encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# Parser fixture tests
# ---------------------------------------------------------------------------

def test_trailing_newline(tmp_path):
    path = write_menu(tmp_path, "menu.txt", "B1;Thin Crust;149\n")
    items = load_menu(path)
    assert len(items) == 1
    assert items[0] == {"id": "B1", "name": "Thin Crust", "price": 149.0}


def test_blank_middle_line(tmp_path):
    path = write_menu(tmp_path, "menu.txt", "B1;Thin Crust;149\n\nB2;Thick Crust;179\n")
    items = load_menu(path)
    assert len(items) == 2
    assert items[0]["id"] == "B1"
    assert items[1]["id"] == "B2"


def test_no_price_skipped(tmp_path):
    # B6;Stuffed; — price field is empty string
    path = write_menu(tmp_path, "menu.txt", "B1;Thin Crust;149\nB6;Stuffed;\n")
    items = load_menu(path)
    assert len(items) == 1
    assert items[0]["id"] == "B1"


def test_empty_name_skipped(tmp_path):
    # B7;;199 — name is empty
    path = write_menu(tmp_path, "menu.txt", "B1;Thin Crust;149\nB7;;199\n")
    items = load_menu(path)
    assert len(items) == 1
    assert items[0]["id"] == "B1"


def test_extra_semicolon(tmp_path):
    # B8;Weird;Name;199 — extra ; → name "Weird;Name"
    path = write_menu(tmp_path, "menu.txt", "B8;Weird;Name;199\n")
    items = load_menu(path)
    assert len(items) == 1
    assert items[0]["id"] == "B8"
    assert items[0]["name"] == "Weird;Name"
    assert items[0]["price"] == 199.0


def test_non_numeric_price_skipped(tmp_path):
    # B9;Bad;abc — non-numeric price
    path = write_menu(tmp_path, "menu.txt", "B1;Thin Crust;149\nB9;Bad;abc\n")
    items = load_menu(path)
    assert len(items) == 1
    assert items[0]["id"] == "B1"


def test_negative_price_skipped(tmp_path):
    # B10;Neg;-50 — negative price
    path = write_menu(tmp_path, "menu.txt", "B1;Thin Crust;149\nB10;Neg;-50\n")
    items = load_menu(path)
    assert len(items) == 1
    assert items[0]["id"] == "B1"


def test_spaces_around_fields(tmp_path):
    # Spaces around each field should be stripped
    path = write_menu(tmp_path, "menu.txt", " B1 ; Thin Crust ; 149 \n")
    items = load_menu(path)
    assert len(items) == 1
    assert items[0] == {"id": "B1", "name": "Thin Crust", "price": 149.0}


def test_empty_file_raises_menu_error(tmp_path):
    path = write_menu(tmp_path, "menu.txt", "")
    with pytest.raises(MenuError):
        load_menu(path)


def test_missing_file_raises_menu_error(tmp_path):
    path = str(tmp_path / "nonexistent.txt")
    with pytest.raises(MenuError):
        load_menu(path)


def test_all_malformed_raises_menu_error(tmp_path):
    # File exists but every line is malformed — should raise MenuError
    path = write_menu(tmp_path, "menu.txt", "B9;Bad;abc\nB10;Neg;-50\nB7;;199\n")
    with pytest.raises(MenuError):
        load_menu(path)


# ---------------------------------------------------------------------------
# Provided-file count tests
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(__file__)


def test_provided_bases_count():
    items = load_menu(os.path.join(BASE_DIR, "Types_of_Base.txt"))
    assert len(items) == 5


def test_provided_pizzas_count():
    items = load_menu(os.path.join(BASE_DIR, "Types_of_Pizza.txt"))
    assert len(items) == 8


def test_provided_toppings_count():
    items = load_menu(os.path.join(BASE_DIR, "Types_of_Toppings.txt"))
    assert len(items) == 10


def test_known_base_item():
    # B3 = Cheese Burst @ 229.0 (golden bill oracle item)
    items = load_menu(os.path.join(BASE_DIR, "Types_of_Base.txt"))
    b3 = next((i for i in items if i["id"] == "B3"), None)
    assert b3 is not None
    assert b3["name"] == "Cheese Burst"
    assert b3["price"] == 229.0


def test_order_preserved(tmp_path):
    # Result list must preserve file order
    path = write_menu(tmp_path, "menu.txt", "B3;C;300\nB1;A;100\nB2;B;200\n")
    items = load_menu(path)
    assert [i["id"] for i in items] == ["B3", "B1", "B2"]


# ---------------------------------------------------------------------------
# Validator tests — 8 mandated edge cases
# ---------------------------------------------------------------------------

_NAME_ERR = "Name must be 2–40 letters (spaces allowed), no numbers or symbols."
_PHONE_ERR = "Phone must be exactly 10 digits and start with 6, 7, 8, or 9."
_QTY_ERR = "Quantity must be a whole number between 1 and 10."
_QTY_MAX_ERR = "Maximum 10 pizzas per order."
_PAYMENT_ERR = "Choose payment: 1 = Cash, 2 = Card, 3 = UPI."


def _choice_err(n):
    return f"Enter the item NUMBER from the list (1–{n})."


# --- Edge case #1: Name only spaces ---
def test_name_only_spaces():
    ok, msg = validate_name("   ")
    assert ok is False
    assert msg == _NAME_ERR


# --- Edge case #2: Phone starting with 1 ---
def test_phone_starts_with_1():
    ok, msg = validate_phone("1234567890")
    assert ok is False
    assert msg == _PHONE_ERR


# --- Edge case #3: Qty 0 and 11 ---
def test_qty_zero():
    ok, msg = validate_qty("0")
    assert ok is False
    assert msg == _QTY_ERR


def test_qty_eleven():
    ok, msg = validate_qty("11")
    assert ok is False
    assert msg == _QTY_MAX_ERR


# --- Edge case #4: Choice 0 and >n ---
def test_choice_zero():
    ok, msg = validate_choice("0", 8)
    assert ok is False
    assert msg == _choice_err(8)


def test_choice_greater_than_n():
    ok, msg = validate_choice("9", 8)
    assert ok is False
    assert msg == _choice_err(8)


# --- Edge case #5: Price entered as item number (229 > N=8) ---
def test_choice_price_as_item_number():
    ok, msg = validate_choice("229", 8)
    assert ok is False
    assert msg == _choice_err(8)


# --- Edge case #6: Empty input at every field ---
def test_empty_name():
    ok, msg = validate_name("")
    assert ok is False
    assert msg == _NAME_ERR


def test_empty_phone():
    ok, msg = validate_phone("")
    assert ok is False
    assert msg == _PHONE_ERR


def test_empty_qty():
    ok, msg = validate_qty("")
    assert ok is False
    assert msg == _QTY_ERR


def test_empty_choice():
    ok, msg = validate_choice("", 8)
    assert ok is False
    assert msg == _choice_err(8)


def test_empty_payment():
    ok, msg = validate_payment("")
    assert ok is False
    assert msg == _PAYMENT_ERR


# --- Edge case #7: Non-integer qty ---
def test_qty_non_integer_word():
    ok, msg = validate_qty("three")
    assert ok is False
    assert msg == _QTY_ERR


def test_qty_non_integer_decimal():
    ok, msg = validate_qty("2.5")
    assert ok is False
    assert msg == _QTY_ERR


# ---------------------------------------------------------------------------
# Boundary tests
# ---------------------------------------------------------------------------

def test_qty_boundary_low():
    assert validate_qty("1") == (True, 1)


def test_qty_boundary_high():
    assert validate_qty("10") == (True, 10)


def test_choice_boundary_low():
    assert validate_choice("1", 8) == (True, 1)


def test_choice_boundary_high():
    assert validate_choice("8", 8) == (True, 8)


def test_valid_name():
    assert validate_name("Rajan Sharma") == (True, "Rajan Sharma")


def test_valid_phone():
    assert validate_phone("9876543210") == (True, "9876543210")


def test_payment_cash():
    assert validate_payment("1") == (True, "Cash")


def test_payment_card():
    assert validate_payment("2") == (True, "Card")


def test_payment_upi():
    assert validate_payment("3") == (True, "UPI")


def test_name_with_digits_rejected():
    ok, msg = validate_name("Ram123")
    assert ok is False
    assert msg == _NAME_ERR


def test_name_too_short():
    ok, msg = validate_name("A")
    assert ok is False
    assert msg == _NAME_ERR


def test_phone_too_short():
    ok, msg = validate_phone("987654321")
    assert ok is False
    assert msg == _PHONE_ERR


def test_payment_invalid():
    ok, msg = validate_payment("4")
    assert ok is False
    assert msg == _PAYMENT_ERR


# ---------------------------------------------------------------------------
# Pricing tests — compute_bill
# ---------------------------------------------------------------------------

_CHEESE_BURST = {"id": "B3", "name": "Cheese Burst", "price": 229.0}
_BBQ_CHICKEN  = {"id": "P7", "name": "BBQ Chicken",  "price": 379.0}
_EXTRA_CHEESE = {"id": "T2", "name": "Extra Cheese",  "price": 69.0}


def test_golden_bill():
    bill = compute_bill(_CHEESE_BURST, _BBQ_CHICKEN, _EXTRA_CHEESE, qty=5)
    assert bill["unit_price"] == 677.0
    assert bill["subtotal"] == 3385.0
    assert bill["discount"] == 338.50
    assert bill["post_discount"] == 3046.50
    assert bill["gst"] == 548.37
    assert bill["total"] == 3594.87
    assert bill["discount_applied"] is True
    assert bill["quantity"] == 5


def test_discount_boundary_qty4():
    bill = compute_bill(_CHEESE_BURST, _BBQ_CHICKEN, _EXTRA_CHEESE, qty=4)
    assert bill["discount"] == 0.00
    assert bill["discount_applied"] is False
    assert bill["subtotal"] == 677.0 * 4
    assert bill["post_discount"] == 677.0 * 4
    gst = round(677.0 * 4 * 0.18, 2)
    assert bill["gst"] == gst
    assert bill["total"] == round(677.0 * 4 + gst, 2)


def test_discount_boundary_qty5():
    bill = compute_bill(_CHEESE_BURST, _BBQ_CHICKEN, _EXTRA_CHEESE, qty=5)
    assert bill["discount_applied"] is True
    assert bill["discount"] == round(3385.0 * 0.10, 2)


def test_no_discount_case():
    base    = {"id": "B1", "name": "Thin Crust",   "price": 100.0}
    pizza   = {"id": "P1", "name": "Margherita",   "price": 200.0}
    topping = {"id": "T1", "name": "Olives",       "price": 50.0}
    bill = compute_bill(base, pizza, topping, qty=2)
    assert bill["unit_price"] == 350.0
    assert bill["subtotal"] == 700.0
    assert bill["discount"] == 0.00
    assert bill["discount_applied"] is False
    assert bill["post_discount"] == 700.0
    assert bill["gst"] == round(700.0 * 0.18, 2)
    assert bill["total"] == round(700.0 + round(700.0 * 0.18, 2), 2)


# ---------------------------------------------------------------------------
# Bill HTML render tests
# ---------------------------------------------------------------------------

def test_render_bill_html_golden_contains_required():
    bill = compute_bill(_CHEESE_BURST, _BBQ_CHICKEN, _EXTRA_CHEESE, qty=5)
    html = render_bill_html(bill, "Rajan")
    assert "₹3594.87" in html
    assert "Subtotal" in html
    assert "Discount" in html
    assert "GST" in html
    assert "Total" in html
    assert "Rajan" in html


def test_render_bill_html_no_discount_shows_zero():
    bill = compute_bill(_CHEESE_BURST, _BBQ_CHICKEN, _EXTRA_CHEESE, qty=4)
    html = render_bill_html(bill, "Alice")
    assert "₹0.00" in html
