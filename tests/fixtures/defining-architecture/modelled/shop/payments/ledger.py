import decimal

_ENTRIES = []


def record(token, amount):
    _ENTRIES.append({"token": token, "amount": decimal.Decimal(amount)})


def entries_for(day):
    return list(_ENTRIES)
