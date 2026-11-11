from shop.orders import service


def post_order(item, quantity):
    return service.write_order(item, quantity)
