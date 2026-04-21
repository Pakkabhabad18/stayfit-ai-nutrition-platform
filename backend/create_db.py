import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn = psycopg2.connect(user="postgres", password="1625", host="localhost", port="5432")
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()
try:
    cursor.execute("CREATE DATABASE stayfit;")
    print("Database 'stayfit' created successfully.")
except psycopg2.errors.DuplicateDatabase:
    print("Database 'stayfit' already exists.")
finally:
    cursor.close()
    conn.close()
