"""数据库连接"""
import pymysql
from config import MYSQL_CONFIG

def get_db_connection():
    connection = pymysql.connect(**MYSQL_CONFIG)
    return connection

