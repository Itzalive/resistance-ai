from shop.orders import service
from shop.payments import card


def refund(order_id, token, amount):
    order = service.read_order(order_id)
    return card.charge(token, -min(amount, order["total"]))
