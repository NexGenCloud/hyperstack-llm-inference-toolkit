import uuid
import typing

from sqlalchemy.orm import Session
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
from marshmallow_sqlalchemy import SQLAlchemySchema
from marshmallow import fields

from utils.db import db


class APIKey(db.Model):
    """
    A table to contain api keys for a user
    """

    __tablename__ = "api_key"

    id = db.Column(db.Integer, primary_key=True, index=True)
    user_id = db.Column(db.String(255), index=True)
    api_key = db.Column(
        StringEncryptedType(db.String(), "SECRET_KEY", AesEngine, "pkcs5", length=255),
        unique=True,
        index=True,
    )
    allowed_rpm = db.Column(db.Integer, default=20)
    enabled = db.Column(db.Boolean, default=True)

    @classmethod
    def get_or_create(
        cls: typing.Self, session: Session, user_id: str, allowed_rpm: int = None
    ) -> typing.Self:
        api_key = session.query(cls).filter_by(user_id=str(user_id)).first()
        if not api_key:
            api_key = cls(
                user_id=user_id,
                api_key=str(uuid.uuid4()),
            )
            session.add(api_key)
            session.commit()
        api_key.allowed_rpm = allowed_rpm if allowed_rpm else api_key.allowed_rpm
        api_key.enabled = True
        return api_key


class APIKeySchema(SQLAlchemySchema):
    class Meta:
        model = APIKey

    id = fields.Integer()
    user_id = fields.String()
    api_key = fields.String()
    allowed_rpm = fields.Integer()
    enabled = fields.Boolean()
