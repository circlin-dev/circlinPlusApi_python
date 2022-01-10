from sqlalchemy import create_engine
from config.database import DB_URL
from sqlalchemy import Column

db = create_engine(DB_URL)

class Bodylab(db.Model):
  __tablename__ = "bodydata"