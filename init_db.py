
from app.db.session import Base, engine
from app.db.models import DocumentMetadata, InterviewBooking


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")

    print("Tables:")
    for table_name in Base.metadata.tables:
        print(f"- {table_name}")


if __name__ == "__main__":
    init_db()
