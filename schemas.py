from datetime import date
from pydantic import BaseModel

class TransactionBase(BaseModel):
    id: str
    timestamp: date
    gas_price: int
    gas_used: int
    transaction_fee_usdt: float