DB = {
  "user": "circlin",
  "password": "circlinDev2019!",
  "host": "circlin-test.cse1vltsv4xu.ap-northeast-2.rds.amazonaws.com",
  "port": 3306,
  "database": "circlin_plus_test"
}

DB_URL = f"mysql+mysqlconnector://{DB['user']}:{DB['password']}@{DB['host']}:{DB['port']}/{DB['database']}?charset=utf8"
