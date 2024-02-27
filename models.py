from sqlalchemy import Column, String, Integer, Float, DateTime
from database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(50), primary_key=True, index=True)
    timestamp = Column(DateTime)
    gas_price = Column(Integer)
    gas_used = Column(Integer)
    transaction_fee_usdt = Column(Float)
