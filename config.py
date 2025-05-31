# MySQL 配置
import pymysql.cursors
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'mysql_password',
    'database': 'my_database',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

config = {
    "secret_key" : "my_secret_key"
}