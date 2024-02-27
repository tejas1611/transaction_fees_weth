from sqlalchemy.orm import Session

import models
import schemas


def get_transaction(db: Session, hash: str):
    return db.query(models.Transaction).filter(models.Transaction.id == hash).first()

def create_transaction(db: Session, transaction: schemas.TransactionBase):
    db_transaction = models.Transaction(**transaction.dict())
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction
