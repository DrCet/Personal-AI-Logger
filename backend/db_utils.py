from database import Base, engine
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--create-tables',
        help='Create all database tables for the first time',
        default=False,
        action='store_true'
    )

    args = parser.parse_args()
    if args.create_tables:
        create_tables()


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Database tables created")

if __name__ == '__main__':
    main()