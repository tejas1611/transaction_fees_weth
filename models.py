from sqlalchemy import Column, String, Integer, Float, Date
from database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(50), primary_key=True, index=True)
    timestamp = Column(Date)
    gas_price = Column(Integer)
    gas_used = Column(Integer)
    transaction_fee_usdt = Column(Float)
