from inventory_manager import (Inventory, PhysicalProduct, DigitalProduct,
                               SubscriptionProduct, Supplier)

supplier = Supplier("S1", "Acme Supply", "acme@example.com")
inventory = Inventory()
inventory.add_product(PhysicalProduct("P001", "Laptop", 1200.00, 10, 2.5, supplier))
inventory.add_product(DigitalProduct("D001", "E-Book", 15.00, 100, 3.2, supplier))
inventory.add_product(SubscriptionProduct("S001", "Streaming Plan", 9.99, 50, 12, supplier))

# PREDICTIONS - written BEFORE running, keyed by product ID
predicted = {
    "P001": "...",   # your prediction
    "D001": "...",
    "S001": "...",
}

# ONE loop over the common Product type: no isinstance, no separate loops
for product in inventory:
    product.display_information()
    actual = product.get_fulfilment_info()
    print(actual)
    print("MATCH" if actual == predicted[product.product_id] else f"MISMATCH - predicted: {predicted[product.product_id]!r}")
    print()