import typing

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Session, relationship
from marshmallow_sqlalchemy import SQLAlchemySchema
from marshmallow import fields

from utils.db import db


class ReplicaVMStatus:
    PENDING = 'PENDING'
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'

    CHOICES = [PENDING, SUCCESS, FAILED]


class Replica(db.Model):
    """
    A table to store models in db
    """

    __tablename__ = 'replicas'

    id = db.Column(db.Integer, primary_key=True, index=True)
    model_id = db.Column(db.Integer, ForeignKey('llm_models.id'), nullable=False)
    endpoint = db.Column(db.String(255))
    rate_limit = db.Column(db.Integer)
    flavor_name = db.Column(db.String(255))
    vm_status = db.Column(db.String(255), default=ReplicaVMStatus.CHOICES[0])
    name = db.Column(db.String(255))
    environment_name = db.Column(db.String(255))
    image_name = db.Column(db.String(255))
    assign_floating_ip = db.Column(db.Boolean)
    run_command = db.Column(db.TEXT())
    key_name = db.Column(db.String(255))
    vm_id = db.Column(db.Integer)
    error_message = db.Column(db.TEXT())

    # Relationships
    llm_model = relationship('LLMModel', foreign_keys=[model_id])

    @classmethod
    def create(
        cls: typing.Self,
        session: Session,
        **data: typing.Dict[str, typing.Any]
    ) -> typing.Self:
        """
        Create a metric record in the database
        """
        replica = cls()
        for key, value in data.items():
            if hasattr(cls, key):
                setattr(replica, key, value)

        session.add(replica)
        session.commit()
        return replica

    @classmethod
    def update(
        cls: typing.Self,
        session: Session,
        replica: typing.Self,
        **data: typing.Dict[str, typing.Any]
    ) -> typing.Self:
        """
        Update a metric record in the database
        """
        for key, value in data.items():
            if hasattr(cls, key):
                setattr(replica, key, value)

        session.commit()
        return replica


class ReplicaSchema(SQLAlchemySchema):
    class Meta:
        model = Replica
        include_relationships = True

    id = fields.Integer()
    model_id = fields.Integer()
    endpoint = fields.String()
    rate_limit = fields.Integer()
    flavor_name = fields.String()
    vm_status = fields.String()
    name = fields.String()
    environment_name = fields.String()
    image_name = fields.String()
    assign_floating_ip = fields.Boolean()
    run_command = fields.String()
    key_name = fields.String()
    vm_id = fields.Integer()
    error_message = fields.String()

    # Relationships
    model = fields.Nested('LLMModelSchema')
