from sqlalchemy import Column, Table
from sqlalchemy.sql.sqltypes import Integer, DateTime, String
from config.db import meta

users = Table(
    "users", meta,
    Column('id', Integer, primary_key=True),
    Column('name', String(255)),
    Column('img', String(255)),
    Column('encoding', String(4096))
)

logs = Table(
    "logs", meta,
    Column('id', Integer, primary_key=True),
    Column('datetime', DateTime),
    Column('face_id', String(255)),
    Column('face_img', String)
)

account_user = Table(
    "account_user", meta,
    Column("id", Integer, primary_key=True),
    Column("name", String(255)),
    Column("email", String(255)),
    Column("password", String(255)),
    Column("access_token", String(512)),
    Column("refresh_token", String(512))
)

meta.create_all()