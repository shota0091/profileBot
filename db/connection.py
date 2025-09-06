import os, pymysql
from dotenv import load_dotenv
load_dotenv()

def get_conn():
    return pymysql.connect(
        host=os.getenv("Dmysql_host","127.0.0.1"),
        port=int(os.getenv("mysql_port","3306")),
        user=os.getenv("mysql_user"),
        password=os.getenv("mysql_password"),
        database=os.getenv("mysql_db","profile"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True,
    )
