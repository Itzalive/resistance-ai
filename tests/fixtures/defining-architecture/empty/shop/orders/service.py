import json
from shop.inventory import stock
from shop.orders import models


def write_order(item, quantity):
    stock.reserve(item, quantity)
    order = models.Order(item, quantity, quantity * 5)
    return json.loads(json.dumps(order.__dict__))


def read_order(order_id):
    return {"id": order_id, "total": 5}
