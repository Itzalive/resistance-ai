import dataclasses


@dataclasses.dataclass
class Order:
    item: str
    quantity: int
    total: int
