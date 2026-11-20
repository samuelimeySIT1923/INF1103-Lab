"""
Acceptance test: one section per requirement.

Run from the same folder as inventory_manager.py:
    python test_requirements.py

Two kinds of evidence are used:
  * STRUCTURAL - the source of inventory_manager.py is parsed (ast) and inspected.
  * BEHAVIOURAL - the real code is run with simulated input / temporary files.
"""
import ast
import contextlib
import io
import json
import math
import os
import sys
import tempfile
from unittest.mock import patch

import inventory_manager as im
from inventory_manager import (
    BulkDiscount,
    DigitalProduct,
    DiscountStrategy,
    FileHandling,
    Inventory,
    MainProgram,
    NoDiscount,
    Order,
    OrderLine,
    PercentageDiscount,
    PhysicalProduct,
    ProductFactory,
    SubscriptionProduct,
    Supplier,
    create_product,
    load_products,
    read_number,
    get_positive_float,
)

REQUIREMENTS = {
    1: "Order totals go through a DiscountStrategy; Order has no discount if/elif logic",
    2: "A new discount strategy can be added without changing Order",
    3: "The strategy on an existing order can be changed with set_discount()",
    4: "Products are created through ProductFactory, not directly",
    5: "An unknown product type raises a ValueError with a clear message",
    6: "Invalid prices, stock quantities and order quantities are rejected",
    7: "Invalid user input is handled without crashing and the user is asked again",
    8: "A missing products file is handled gracefully",
    9: "Bad rows are reported and skipped; valid rows still load",
    10: "Each except catches a specific exception",
}
results = {n: [] for n in REQUIREMENTS}
current = 0


def section(n):
    global current
    current = n
    print("\n" + "=" * 74)
    print(f"REQUIREMENT {n}: {REQUIREMENTS[n]}")
    print("=" * 74)


def check(label, actual, expected):
    ok = actual == expected
    results[current].append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if not ok:
        print(f"       expected: {expected!r}")
        print(f"       actual:   {actual!r}")


def expect_error(label, error_type, message, func):
    try:
        func()
    except error_type as e:
        ok = message is None or str(e) == message
        results[current].append(ok)
        print(f"[{'PASS' if ok else 'FAIL'}] {label}  ->  {type(e).__name__}: {e}")
        if not ok:
            print(f"       expected message: {message!r}")
    else:
        results[current].append(False)
        print(f"[FAIL] {label}: nothing was raised")


def run_capturing(func):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        value = func()
    return value, buf.getvalue()


@contextlib.contextmanager
def in_temp_dir():
    """Run in an empty folder so the program never touches a real inventory.json."""
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            yield tmp
        finally:
            os.chdir(cwd)


# ---- source tree for the structural checks ----------------------------------
TREE = ast.parse(open(im.__file__, encoding="utf-8").read())


def find_class(name):
    return next(n for n in TREE.body if isinstance(n, ast.ClassDef) and n.name == name)


def find_method(cls, name):
    return next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == name)


# ---- shared fixtures ---------------------------------------------------------
SUPPLIER = Supplier("S1", "Acme Supplies", "sales@acme.example")
GIVEN_CSV = """product_type,product_id,name,price,stock_quantity
physical,P001,Desk Lamp,25.00,10
digital,D001,Photo Editor,49.90,100
service,S001,Installation,30.00,5
physical,P002,Office Chair,abc,3
physical,P003,Monitor Stand,39.50,7
"""
MESSY_CSV = """product_type,product_id,name,price,stock_quantity
physical,P1,Lamp,25.00,10
digital,D1,Editor,49.90,100
physical,P1,Duplicate Lamp,5.00,1
physical,P2,Free Thing,0,5
physical,P3,Negative Stock,10.00,-2
physical,P4,Fractional Stock,10.00,2.5
physical,P5,Too Short

Physical,P6,Wrong Case,1.00,1
subscription,B1,Plan,20.00,3
"""


def order_of_250(discount=None):
    """3 lines built THROUGH the factory: 1 x 100 + 2 x 25 + 2 x 50 = 250."""
    order = Order("ORD-1") if discount is None else Order("ORD-1", discount)
    order.add_order_line(ProductFactory.create("physical", "P1", "Keyboard", 100.0, 10, SUPPLIER, 0.8), 1)
    order.add_order_line(ProductFactory.create("digital", "D1", "Ebook", 25.0, 99, SUPPLIER, 12.5), 2)
    order.add_order_line(ProductFactory.create("subscription", "B1", "Plan", 50.0, 99, SUPPLIER, 12), 2)
    return order


# =============================================================================
section(1)
# =============================================================================
class SpyStrategy(DiscountStrategy):
    def __init__(self):
        self.seen = []

    def apply(self, total):
        self.seen.append(total)
        return 123.0  # a value that cannot come from the order lines


spy = SpyStrategy()
order = order_of_250(spy)
check("calculate_total() returns whatever the strategy returns (123.0, not 250)", order.calculate_total(), 123.0)
check("the strategy was handed the line sum (250) exactly once", spy.seen, [250.0])

order_cls = find_class("Order")
branches = [n for n in ast.walk(order_cls) if isinstance(n, (ast.If, ast.IfExp))]
print("   conditionals found inside Order:", [f"{type(n).__name__}: {ast.unparse(n.test)}" for n in branches])
check("Order's only conditionals are a default and a type guard (nothing chooses a discount)",
      sorted(ast.unparse(n.test) for n in branches),
      ["not isinstance(discount, DiscountStrategy)", "order_discount is not None"])
check("no 'elif' chain anywhere in Order",
      any(isinstance(n, ast.If) and len(n.orelse) == 1 and isinstance(n.orelse[0], ast.If) for n in ast.walk(order_cls)),
      False)
check("calculate_total() contains no if/else at all",
      [n for n in ast.walk(find_method(order_cls, "calculate_total")) if isinstance(n, (ast.If, ast.IfExp))], [])
names_in_order = {n.id for n in ast.walk(order_cls) if isinstance(n, ast.Name)}
check("Order never mentions PercentageDiscount or BulkDiscount",
      names_in_order & {"PercentageDiscount", "BulkDiscount"}, set())
strings_in_order = " ".join(n.value.lower() for n in ast.walk(order_cls)
                            if isinstance(n, ast.Constant) and isinstance(n.value, str))
check("Order has no discount-name strings to compare against ('percent', 'bulk')",
      ("percent" in strings_in_order, "bulk" in strings_in_order), (False, False))
check("default (nothing passed) behaves as NoDiscount -> 250", order_of_250().calculate_total(), 250.0)

# =============================================================================
section(2)
# =============================================================================
order_source_before = ast.dump(find_class("Order"))


class HalfPriceDiscount(DiscountStrategy):          # brand-new strategy, defined OUTSIDE inventory_manager.py
    def apply(self, total):
        return total / 2


class TieredDiscount(DiscountStrategy):             # another one, with its own rules and its own percentages
    def apply(self, total):
        if total >= 500:
            return total * 80 / 100
        elif total >= 200:
            return total * 90 / 100
        return total


order = order_of_250()
order.set_discount(HalfPriceDiscount())
check("Order accepts HalfPriceDiscount, which it has never heard of: 250 -> 125", order.calculate_total(), 125.0)
order.set_discount(TieredDiscount())
check("Order accepts TieredDiscount: 250 -> 225 (10% tier)", order.calculate_total(), 225.0)
big = Order("BIG", TieredDiscount())
big.add_order_line(ProductFactory.create("physical", "P9", "Server", 600.0, 1, SUPPLIER, 20.0), 1)
check("TieredDiscount: 600 -> 480 (20% tier)", big.calculate_total(), 480.0)
check("Order's source is byte-for-byte the same after adding two strategies",
      ast.dump(find_class("Order")), order_source_before)
order_source_text = ast.unparse(find_class("Order"))
check("neither new class is mentioned anywhere in Order",
      ("HalfPrice" in order_source_text, "Tiered" in order_source_text), (False, False))
expect_error("an object that is NOT a DiscountStrategy is refused", TypeError, None,
             lambda: order.set_discount("10% off"))

# =============================================================================
section(3)
# =============================================================================
order = order_of_250()
same_order = order
check("starts with no discount: 250", order.calculate_total(), 250.0)
order.set_discount(BulkDiscount(200, 20))
check("set_discount(BulkDiscount(200, 20)) -> 230", order.calculate_total(), 230.0)
order.set_discount(PercentageDiscount(10))
check("set_discount(PercentageDiscount(10)) on the SAME order -> 225 (replaces, does not stack)", order.calculate_total(), 225.0)
order.set_discount(NoDiscount())
check("set_discount(NoDiscount()) -> back to 250", order.calculate_total(), 250.0)
order.set_discount(HalfPriceDiscount())
check("set_discount(HalfPriceDiscount()) -> 125", order.calculate_total(), 125.0)
check("it was the same Order object and its 3 lines were never touched", (order is same_order, len(order.order_lines)), (True, 3))
shared = PercentageDiscount(10)
a, b = order_of_250(), order_of_250()
a.set_discount(shared)
b.set_discount(shared)
b.set_discount(NoDiscount())
check("changing one order's strategy leaves another order sharing the old one alone",
      (a.calculate_total(), b.calculate_total()), (225.0, 250.0))

# =============================================================================
section(4)
# =============================================================================
constructed_in = []
subclass_names = {"PhysicalProduct", "DigitalProduct", "SubscriptionProduct"}


class Finder(ast.NodeVisitor):
    def __init__(self):
        self.stack = []

    def visit_ClassDef(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_FunctionDef(self, node):
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in subclass_names:
            constructed_in.append(".".join(self.stack))
        self.generic_visit(node)


Finder().visit(TREE)
check("source scan: every direct construction is inside ProductFactory.create",
      sorted(set(constructed_in)), ["ProductFactory.create"])
check("source scan: exactly one constructor call per type (3)", len(constructed_in), 3)

original_create = ProductFactory.create
dict_record = {"id": "P1", "product_name": "Mug", "price": 9.5, "stock": 3, "type": "physical", "weight": 0.4,
               "supplier": {"supplier_id": "S", "supplier_name": "A", "contact_email": "e"}}
with patch.object(ProductFactory, "create", wraps=original_create) as factory_spy:
    create_product(dict_record)
check("runtime: create_product(dict) went through the factory", factory_spy.call_count, 1)

with in_temp_dir() as tmp:
    json_path = os.path.join(tmp, "inv.json")
    products = [original_create("physical", "P1", "A", 1.0, 1, SUPPLIER, 1.0),
                original_create("digital", "D1", "B", 1.0, 1, SUPPLIER, 1.0),
                original_create("subscription", "B1", "C", 1.0, 1, SUPPLIER, 1)]
    with open(json_path, "w") as f:
        json.dump({"products": [p.to_dict() for p in products], "transactions": []}, f)
    with patch.object(ProductFactory, "create", wraps=original_create) as factory_spy:
        loaded, _ = FileHandling(json_path).load_inventory()
    check("runtime: loading inventory.json built 3 products, all through the factory",
          (len(loaded), factory_spy.call_count), (3, 3))

    answers = ["ID1", "Thing", "9.99", "5", "S9", "Sup", "s@x.y", "2", "40"]
    with patch("builtins.input", side_effect=answers), \
            patch.object(ProductFactory, "create", wraps=original_create) as factory_spy:
        typed, _ = run_capturing(lambda: MainProgram().prompt_for_product())
    check("runtime: the 'create product' menu went through the factory (digital)",
          (type(typed), factory_spy.call_count), (DigitalProduct, 1))

    csv_path = os.path.join(tmp, "products.csv")
    with open(csv_path, "w", newline="") as f:
        f.write(GIVEN_CSV)
    with patch.object(ProductFactory, "create", wraps=original_create) as factory_spy:
        run_capturing(lambda: load_products(csv_path, Inventory([], []), SUPPLIER))
    check("runtime: load_products used the factory for each row that reached it (4 of 5; the 'abc' price fails first)",
          factory_spy.call_count, 4)

# =============================================================================
section(5)
# =============================================================================
expect_error("ProductFactory.create('food', ...)", ValueError, "Unknown product type: food",
             lambda: ProductFactory.create("food", "X", "n", 1.0, 1, SUPPLIER, 1))
expect_error("exact match only: 'Physical' (capital P)", ValueError, "Unknown product type: Physical",
             lambda: ProductFactory.create("Physical", "X", "n", 1.0, 1, SUPPLIER, 1))
expect_error("create_product() on a record with type 'food'", ValueError, "Unknown product type: food",
             lambda: create_product({"id": "X", "product_name": "n", "price": 1.0, "stock": 1, "type": "food"}))
with in_temp_dir() as tmp:
    p = os.path.join(tmp, "p.csv")
    with open(p, "w", newline="") as f:
        f.write(GIVEN_CSV)
    _, out = run_capturing(lambda: load_products(p, Inventory([], []), SUPPLIER))
    check("load_products reports it with the line number and the type",
          any("line 4" in l and "Unknown product type: service" in l for l in out.splitlines()), True)

# =============================================================================
section(6)
# =============================================================================
PRICE, STOCK, QTY = ("Price must be greater than zero.", "Stock quantity cannot be negative.",
                     "Quantity must be greater than zero.")
for label, make in [("PhysicalProduct", lambda price, stock: PhysicalProduct("P", "n", price, stock, 1.0, SUPPLIER)),
                    ("DigitalProduct", lambda price, stock: DigitalProduct("D", "n", price, stock, 1.0, SUPPLIER)),
                    ("SubscriptionProduct", lambda price, stock: SubscriptionProduct("B", "n", price, stock, 1, SUPPLIER))]:
    for bad in (0, -1, math.nan):
        expect_error(f"{label}: price {bad}", ValueError, PRICE, lambda m=make, v=bad: m(v, 1))
    expect_error(f"{label}: stock -1", ValueError, STOCK, lambda m=make: m(10.0, -1))
    make(0.01, 0)  # boundary values must be ACCEPTED: price 0.01, stock 0
    results[current].append(True)
    print(f"[PASS] {label}: boundaries accepted (price 0.01, stock 0)")
expect_error("ProductFactory.create with price 0", ValueError, PRICE,
             lambda: ProductFactory.create("digital", "D", "n", 0, 1, SUPPLIER, 1.0))
p = ProductFactory.create("physical", "P1", "Keyboard", 100.0, 10, SUPPLIER, 0.8)
expect_error("stock setter: p.stock = -1", ValueError, STOCK, lambda: setattr(p, "stock", -1))
expect_error("update_stock(-1)", ValueError, STOCK, lambda: p.update_stock(-1))
check("a rejected change leaves the old stock in place", p.stock, 10)
expect_error("OrderLine quantity 0", ValueError, QTY, lambda: OrderLine(p, 0))
expect_error("OrderLine quantity -1", ValueError, QTY, lambda: OrderLine(p, -1))
line = OrderLine(p, 2)
expect_error("line.quantity = 0 after construction", ValueError, QTY, lambda: setattr(line, "quantity", 0))
check("a rejected change leaves the old quantity in place", line.quantity, 2)
order = Order("O")
expect_error("Order.add_order_line(p, 0)", ValueError, QTY, lambda: order.add_order_line(p, 0))
check("no broken line left in the order", len(order.order_lines), 0)
OrderLine(p, 1)
results[current].append(True)
print("[PASS] OrderLine quantity 1 accepted (boundary)")

# =============================================================================
section(7)
# =============================================================================
with patch("builtins.input", side_effect=["abc", "", "0", "-5", "nan", "12.50"]) as fake:
    value, out = run_capturing(lambda: get_positive_float("Price: "))
check("get_positive_float: 5 bad entries (abc, blank, 0, -5, nan) then 12.50 -> returns 12.5", value, 12.5)
check("  ...it asked again each time (6 prompts)", fake.call_count, 6)
check("  ...with the right message for each kind of mistake",
      (out.count("Please enter a valid number, e.g. 12.50"), out.count("Please enter a number greater than zero.")), (2, 3))

with patch("builtins.input", side_effect=["abc", "-3", "7"]) as fake:
    value, out = run_capturing(lambda: read_number("Quantity: ", int))
check("read_number: 'abc' then '-3' then '7' -> returns 7, asked 3 times", (value, fake.call_count), (7, 3))

with in_temp_dir():
    answers = ["P9", "Thing", "abc", "0", "25", "5", "S", "Sup", "s@x.y", "9", "x", "1", "1.0"]
    with patch("builtins.input", side_effect=answers) as fake:
        product, out = run_capturing(lambda: MainProgram().prompt_for_product())
    check("create-product prompts: bad price (abc, 0) and bad type (9, x) re-asked; product built",
          (type(product), product.price), (PhysicalProduct, 25.0))
    check("  ...every answer was consumed, none crashed the prompt", fake.call_count, len(answers))

    with patch("builtins.input", side_effect=["x", "99", "", "8"]):
        _, out = run_capturing(lambda: MainProgram().main())
    check("main menu: 3 invalid choices each get a message, then '8' exits cleanly",
          (out.count("Invalid option. Please choose 1-8."), "Program terminated." in out), (3, True))

    with patch.object(MainProgram, "prompt_for_product", side_effect=ValueError(PRICE)), \
            patch("builtins.input", side_effect=["2", "8"]):
        _, out = run_capturing(lambda: MainProgram().main())
    check("menu safety net: a rejected product prints a message and the menu carries on",
          (f"Product not created: {PRICE}" in out, "Program terminated." in out), (True, True))

# =============================================================================
section(8)
# =============================================================================
with tempfile.TemporaryDirectory() as tmp:
    missing = os.path.join(tmp, "products.csv")
    inv = Inventory([], [])
    _, out = run_capturing(lambda: load_products(missing, inv, SUPPLIER))
    lines = out.strip().splitlines()
    check("missing file: simple message, no crash", lines[0], f"Products file not found: {missing}")
    check("finally still runs", lines[-1], "Load attempt finished.")
    check("no 'products loaded' line (the else block was skipped)", any("loaded" in l for l in lines), False)
    check("inventory untouched", len(list(inv)), 0)

    _, out = run_capturing(lambda: load_products(tmp, Inventory([], []), SUPPLIER))  # a folder, not a file
    lines = out.strip().splitlines()
    check("path is a folder: handled with a 'Could not open' message", lines[0].startswith("Could not open"), True)
    check("finally still runs", lines[-1], "Load attempt finished.")

    check("missing inventory.json is also handled (starts empty)",
          run_capturing(lambda: FileHandling(os.path.join(tmp, "nope.json")).load_inventory())[0], ([], []))

# =============================================================================
section(9)
# =============================================================================
with tempfile.TemporaryDirectory() as tmp:
    p = os.path.join(tmp, "products.csv")
    with open(p, "w", newline="") as f:
        f.write(GIVEN_CSV)
    inv = Inventory([], [])
    _, out = run_capturing(lambda: load_products(p, inv, SUPPLIER))
    lines = out.strip().splitlines()
    check("given products.csv: valid rows P001, D001, P003 loaded", sorted(x.product_id for x in inv), ["D001", "P001", "P003"])
    check("  ...2 bad rows reported (line 4 unknown type, line 5 price 'abc')",
          [l[:14] for l in lines if l.startswith("Skipped")], ["Skipped line 4", "Skipped line 5"])
    check("  ...then the count, then the finally message", lines[-2:], ["3 products loaded.", "Load attempt finished."])

    p2 = os.path.join(tmp, "messy.csv")
    with open(p2, "w", newline="") as f:
        f.write(MESSY_CSV)
    inv = Inventory([], [])
    _, out = run_capturing(lambda: load_products(p2, inv, SUPPLIER))
    lines = out.strip().splitlines()
    check("messy file: only the 3 valid rows loaded (P1, D1, B1)", sorted(x.product_id for x in inv), ["B1", "D1", "P1"])
    check("  ...6 different kinds of bad row reported and skipped (dup id, price 0, stock -2, stock 2.5, 3 columns, 'Physical')",
          len([l for l in lines if l.startswith("Skipped")]), 6)
    check("  ...the first row with a duplicate id won (price 25.0)", inv.find_product("P1").price, 25.0)
    check("  ...a bad row never stopped later rows (B1 comes after all the bad ones)", inv.find_product("B1") is not None, True)

# =============================================================================
section(10)
# =============================================================================
parents = {}
for node in ast.walk(TREE):
    for child in ast.iter_child_nodes(node):
        parents[child] = node


def owner_of(node):
    while node in parents:
        node = parents[node]
        if isinstance(node, ast.FunctionDef):
            return node.name
    return "<module>"


SPECIFIC = {"FileNotFoundError", "OSError", "ValueError", "TypeError", "KeyError", "AttributeError", "json.JSONDecodeError"}
handlers = [n for n in ast.walk(TREE) if isinstance(n, ast.ExceptHandler)]
bare, broad, unknown = [], [], []
print(f"   {len(handlers)} except clauses found:")
for h in sorted(handlers, key=lambda n: n.lineno):
    kinds = ["<bare>"] if h.type is None else [ast.unparse(e) for e in (h.type.elts if isinstance(h.type, ast.Tuple) else [h.type])]
    print(f"     line {h.lineno:>3}  in {owner_of(h):<22} except {', '.join(kinds)}")
    for k in kinds:
        if k == "<bare>":
            bare.append(h.lineno)
        elif k in ("Exception", "BaseException"):
            broad.append(h.lineno)
        elif k not in SPECIFIC:
            unknown.append((h.lineno, k))
check("no bare 'except:'", bare, [])
check("no 'except Exception' / 'except BaseException'", broad, [])
check("every caught type is a specific, known exception", unknown, [])


class ExplodingInventory:
    def add_product(self, product):
        raise RuntimeError("boom")


with tempfile.TemporaryDirectory() as tmp:
    p = os.path.join(tmp, "products.csv")
    with open(p, "w", newline="") as f:
        f.write(GIVEN_CSV)
    buf = io.StringIO()
    raised = None
    with contextlib.redirect_stdout(buf):
        try:
            load_products(p, ExplodingInventory(), SUPPLIER)
        except RuntimeError as e:
            raised = e
    check("an UNEXPECTED error (RuntimeError) is NOT swallowed by 'except ValueError'", str(raised), "boom")
    check("...and finally still ran on the way out", "Load attempt finished." in buf.getvalue(), True)

with patch("builtins.input", side_effect=KeyboardInterrupt):
    expect_error("Ctrl+C is not swallowed by get_positive_float's 'except ValueError'", KeyboardInterrupt, None,
                 lambda: get_positive_float("Price: "))

# =============================================================================
print("\n" + "=" * 74)
print("SUMMARY")
print("=" * 74)
all_ok = True
for n, text in REQUIREMENTS.items():
    passed, total = sum(results[n]), len(results[n])
    ok = passed == total and total > 0
    all_ok &= ok
    print(f"  [{'PASS' if ok else 'FAIL'}] {n:>2}. {text}  ({passed}/{total})")
print("-" * 74)
print(f"  {sum(sum(v) for v in results.values())}/{sum(len(v) for v in results.values())} checks passed")
sys.exit(0 if all_ok else 1)