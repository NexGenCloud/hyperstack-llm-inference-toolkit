import typing

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Session, relationship

from utils.db import db


class ReplicaSecurityRule(db.Model):
    """
    A table to store security rules for an replica
    """
    __tablename__ = 'replica_security_rules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    replica_id = db.Column(db.Integer, ForeignKey('replicas.id'), nullable=False)
    direction = db.Column(db.String(64), nullable=False)
    protocol = db.Column(db.String(64), nullable=False)
    ethertype = db.Column(db.String(64), nullable=False)
    remote_ip_prefix = db.Column(db.String(64), nullable=False)
    port_range_min = db.Column(db.Integer, nullable=False)
    port_range_max = db.Column(db.Integer, nullable=False)

    llm_model = relationship('Replica', foreign_keys=[replica_id])

    @classmethod
    def batch_create(
        cls: typing.Self,
        session: Session,
        data_list: typing.List[typing.Dict[str, typing.Any]]
    ) -> typing.Self:
        """
        Create a metric record in the database
        """
        rules = [cls(**data) for data in data_list]
        session.add_all(rules)
        session.commit()
