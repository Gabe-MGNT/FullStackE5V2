import sqlite3

# create a global connection
db_connection = sqlite3.connect("quizdb.db", check_same_thread=False)
db_connection.isolation_level = None

def get_cursor():
    return db_connection.cursor()
