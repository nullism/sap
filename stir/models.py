import sys
from sqlalchemy import (
    Column, UniqueConstraint, ForeignKey, Float,
    Integer, String, Text, create_engine
)
from sqlalchemy.types import Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
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
    password = Column(String(100))
    is_root = Column(Boolean, default=False)


class UserOrg(BASE):

    __tablename__ = "user_org"
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    user = relationship("User")
    org_id = Column(Integer, ForeignKey("org.id"), primary_key=True)
    org = relationship("Org")

if __name__ == "__main__":

    BASE.metadata.create_all(ENGINE)