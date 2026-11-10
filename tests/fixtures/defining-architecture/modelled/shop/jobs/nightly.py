from shop.orders import service


def restock_order():
    return service.write_order("widget", 10)
