from sqlalchemy import create_engine, MetaData

engine = create_engine("sqlite:///user.db")
meta = MetaData(engine)
conn = engine.connect()