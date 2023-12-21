import sqlite3

DB_CONNECTION = sqlite3.connect("quizdb.db", check_same_thread=False)
DB_CONNECTION.isolation_level = None



