from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

DB_CONFIG = {
  "user": "circlin",
  "password": "circlinDev2019!",
  "host": "circlin-test.cse1vltsv4xu.ap-northeast-2.rds.amazonaws.com",
  "port": 3306,
  "database": "circlin_plus_test"
}

DB_URL = f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}?charset=utf8"
