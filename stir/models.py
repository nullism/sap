import hashlib
import sys
from sqlalchemy import (
    Column, UniqueConstraint, ForeignKey, Float,
    Integer, String, Text, create_engine
)
from sqlalchemy.types import Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship, sessionmaker, scoped_session, backref


BASE = declarative_base()
DB_PATH = "./testdb.db"
ENGINE = create_engine("sqlite:///%s" % (DB_PATH))
BASE.metadata.bind = ENGINE
DB = scoped_session(sessionmaker(bind=ENGINE))

class Log(BASE):

    __tablename__ = "log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")
    ipv4 = Column(String(50))
    message = Column(Text)

class Org(BASE):

    __tablename__ = "org"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(30))
    domain = Column(String(50))


class SshKey(BASE):

    __tablename__ = "ssh_key"
    id = Column(Integer, primary_key=True, autoincrement=True)
    hash = Column(String(50), unique=True)
    text = Column(Text)
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")


class User(BASE):

    __tablename__ = "user"
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(50), unique=True)
    _password = Column("password", String(100))
    is_root = Column(Boolean, default=False)

    @classmethod
    def hash_password(self, password):
        pws = "%sACCX2PTFKM6" % password # TODO make salt configurable
        return hashlib.sha256(pws.encode("utf-8")).hexdigest()

    @hybrid_property
    def password(self):
        return self._password

    @password.setter
    def password(self, value):
        self._password = User.hash_password(value)

class UserOrg(BASE):

    __tablename__ = "user_org"
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    user = relationship("User")
    org_id = Column(Integer, ForeignKey("org.id"), primary_key=True)
    org = relationship("Org")

if __name__ == "__main__":

    BASE.metadata.create_all(ENGINE)

    u1 = User(email="foo@bar.com", password="abc123", is_root=True)
    DB.add(u1) # pylint: disable=E1101
    DB.commit() # pylint: disable=E1101