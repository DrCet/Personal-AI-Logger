DATABASE_URL = 'postgresql://cet:Nvbk%400359408336@localhost:5432/personal_ai_logger'


import psycopg2
conn = psycopg2.connect(DATABASE_URL)
conn.close()
