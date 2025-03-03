DATABASE_URL = 'change your database url here'


import psycopg2
from psycopg2 import Error
def check_permissions():
    try:
        # Establish a connection to the database
        connection = psycopg2.connect(DATABASE_URL)
        cursor = connection.cursor()

        # Get the current user
        cursor.execute("SELECT current_user;")
        current_user = cursor.fetchone()[0]
        print(f"Connected as user: {current_user}")

        # Check USAGE privilege on the public schema
        cursor.execute("SELECT has_schema_privilege(%s, 'public', 'USAGE');", (current_user,))
        usage_privilege = cursor.fetchone()[0]
        print(f"USAGE privilege on 'public' schema: {'Yes' if usage_privilege else 'No'}")

        # Check CREATE privilege on the public schema
        cursor.execute("SELECT has_schema_privilege(%s, 'public', 'CREATE');", (current_user,))
        create_privilege = cursor.fetchone()[0]
        print(f"CREATE privilege on 'public' schema: {'Yes' if create_privilege else 'No'}")

        # Optional: List tables in the public schema to verify access
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
        tables = cursor.fetchall()
        print("Tables in 'public' schema:", [table[0] for table in tables] if tables else "None found")

        cursor.execute("SELECT current_database();")
        current_db = cursor.fetchone()[0]
        print(f"Connected to database: {current_db}")

    except Error as e:
        print(f"Error connecting to the database: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
            print("Database connection closed.")

check_permissions()