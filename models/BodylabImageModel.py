from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String, BIGINT, FLOAT, text, ForeignKey, TIMESTAMP, VARCHAR

db = SQLAlchemy()

class BodylabImageModel(db.Model):
  __tablename__ = "bodylab_image"

  id = db.Column(BIGINT, primary_key = True, nullable=False, autoincrement=True)
  created_at = db.Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
  updated_at = db.Column(TIMESTAMP, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
  bodylab_id = db.Column(BIGINT, ForeignKey('bodaylab.id'), nullable=False)
  original_url = db.Column(VARCHAR(255), nullable=False)
  analyzed_url = db.Column(VARCHAR(255))
  shoulder_ratio = db.Column(FLOAT)
  hip_ratio = db.Column(FLOAT)
  shoulder_width = db.Column(FLOAT)
  hip_width = db.Column(FLOAT)
  nose_to_shoulder_center = db.Column(FLOAT)
  shoulder_center_to_hip_center = db.Column(FLOAT)
  hip_center_to_ankle_center = db.Column(FLOAT)
  whole_body_length = db.Column(FLOAT)
  upperbody_lowerbody = db.Column(FLOAT)
