import typing

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship, Session
from marshmallow_sqlalchemy import SQLAlchemySchema
from marshmallow import fields

from utils.db import db
from tables.api_key import APIKeySchema


class Metric(db.Model):
    """
    A table to contain metrics for an api
    """

    __tablename__ = "metric"

    id = db.Column(db.Integer, primary_key=True, index=True)
    api_key_id = db.Column(db.Integer, ForeignKey('api_key.id'))

    input = db.Column(db.Text)
    created = db.Column(db.Integer)
    model = db.Column(db.String(255))
    choices = db.Column(db.Text)
    prompt_tokens = db.Column(db.Integer)
    total_tokens = db.Column(db.Integer)
    completion_tokens = db.Column(db.Integer)
    duration = db.Column(db.Float)

    # Relationships
    api_key = relationship("APIKey", foreign_keys=[api_key_id])

    @classmethod
    def create(
        cls: typing.Self, session: Session, **metric_data: typing.Dict[str, typing.Any]
    ) -> typing.Self:
        """
        Create a metric record in the database
        """
        db_metric = Metric(**metric_data)
        session.add(db_metric)
        session.commit()
        return db_metric


class MetricSchema(SQLAlchemySchema):
    class Meta:
        model = Metric
        include_relationships = True

    id = fields.Integer()
    api_key_id = fields.Integer()

    input = fields.String()
    created = fields.Integer()
    model = fields.String()
    choices = fields.String()
    prompt_tokens = fields.Integer()
    total_tokens = fields.Integer()
    completion_tokens = fields.Integer()
    duration = fields.Float()

    # Relationships
    api_key = fields.Nested(APIKeySchema)
