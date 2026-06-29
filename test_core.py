import os
import pytest
import core
from core import load_menu, MenuError


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
