from shop.orders import models


def reserve(item, quantity):
    return models.Order(item, quantity, 0)
