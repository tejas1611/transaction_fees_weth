from datetime import datetime
from pydantic import BaseModel

class TransactionBase(BaseModel):
    id: str
    timestamp: datetime
    gas_price: int
    gas_used: int
    transaction_fee_usdt: float