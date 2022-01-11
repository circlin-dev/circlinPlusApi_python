from app import db

class BodylabModel(db.Model):
  __tablename__ = "bodylab"

  id = db.Column(db.BIGINT, primary_key = True, nullable=False, autoincrement=True)
  created_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'))
  updated_at = db.Column(db.TIMESTAMP, nullable=False, server_default=db.text('CURRENT_TIMESTAMP'))
  user_id = db.Column(db.BIGINT, db.ForeignKey('users.id'), nullable=False)
  height = db.Column(db.FLOAT)
  weight = db.Column(db.FLOAT)
  bmi = db.Column(db.FLOAT)
  muscle_mass = db.Column(db.FLOAT)
  fat_mass = db.Column(db.FLOAT)

