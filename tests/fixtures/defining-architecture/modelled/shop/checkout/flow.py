from shop.inventory import stock
from shop.orders import service
from shop.payments import card


def check_out(item, quantity, token):
    order = service.write_order(item, quantity)
    card.charge(token, order["total"])
    return order
