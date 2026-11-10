from shop.payments import ledger


def charge(token, amount):
    ledger.record(token, amount)
    return {"token": token, "amount": amount}
