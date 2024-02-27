from sqlalchemy.orm import Session
from typing import List

import models
import schemas


def get_transaction(db: Session, hash: str):
    return db.query(models.Transaction).filter(models.Transaction.id == hash).first()

def create_transaction(db: Session, transaction: schemas.TransactionBase):
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    return db_transaction

def create_transactions(db: Session, transactions: List[schemas.TransactionBase]):
    db_transactions = [models.Transaction(**transaction.dict()) for transaction in transactions]
    db.add_all(db_transactions)
    db.commit()
    return db_transactions