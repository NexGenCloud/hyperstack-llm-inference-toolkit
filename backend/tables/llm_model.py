from marshmallow_sqlalchemy import SQLAlchemySchema
from marshmallow import fields
from sqlalchemy.orm import relationship

from utils.db import db


class LLMModel(db.Model):
    """
    A table to store llm models in db
    """

    __tablename__ = 'llm_models'

    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String(255), index=True, unique=True)

    replicas = relationship("Replica", back_populates="llm_model")


class LLMModelSchema(SQLAlchemySchema):
    class Meta:
        model = LLMModel

    id = fields.Integer()
    name = fields.String()
