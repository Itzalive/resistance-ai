from shop.payments import ledger


def daily_total(day):
    return sum(entry["amount"] for entry in ledger.entries_for(day))
