import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils.config import DB_PATH

# Log the database path being used
print(f"Database path: {DB_PATH}")

# Create engine and base
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
Base = declarative_base()

# Define feedback model
class Feedback(Base):
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    media_type = Column(String(50), nullable=False)
    result = Column(Text, nullable=False)
    positive = Column(Boolean, nullable=True)
    comment = Column(Text, nullable=True)  # Added comment field for text feedback
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Feedback(id={self.id}, title='{self.title}', positive={self.positive})>"

# Create tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)

def record_feedback(title, media_type, result, positive, comment=None):
    """
    Record user feedback for an insight generation.
    
    Args:
        title (str): The title of the book or movie
        media_type (str): Either 'Book' or 'Movie'
        result (str): The generated insights text
        positive (bool): True for thumbs up, False for thumbs down
        comment (str, optional): Additional text feedback from the user
        
    Returns:
        bool: Success status
    """
    session = None
    try:
        # Create session
        session = Session()
        
        # Check if comment column exists in the table
        from sqlalchemy import inspect
        inspector = inspect(session.bind)
        columns = [col['name'] for col in inspector.get_columns('feedback')]
        has_comment_field = 'comment' in columns
        
        # If the comment column doesn't exist, try to add it
        if not has_comment_field and comment:
            try:
                print("Adding comment column to feedback table...")
                session.execute(text("ALTER TABLE feedback ADD COLUMN comment TEXT"))
                session.commit()
                has_comment_field = True
                print("Comment column added successfully.")
            except Exception as alter_error:
                print(f"Could not add comment column: {str(alter_error)}")
                # Continue without comment column if we can't add it
        
        # Create feedback object with or without comment
        if has_comment_field:
            feedback = Feedback(
                title=title,
                media_type=media_type,
                result=result,
                positive=positive,
                comment=comment
            )
        else:
            # Create feedback without comment for older database schemas
            feedback = Feedback(
                title=title,
                media_type=media_type,
                result=result,
                positive=positive,
            )
            if comment:
                print("Comment provided but not saved due to missing column in database.")
        
        session.add(feedback)
        session.commit()
        session.close()
        return True
    except Exception as e:
        print(f"Error recording feedback: {str(e)}")
        if session:
            session.rollback()
            session.close()
        return False

def get_feedback_stats():
    """
    Get basic statistics about feedback.
    
    Returns:
        dict: Statistics about feedback
    """
    try:
        session = Session()
        total_count = session.query(Feedback).count()
        positive_count = session.query(Feedback).filter(Feedback.positive == True).count()
        negative_count = session.query(Feedback).filter(Feedback.positive == False).count()
        session.close()
        
        return {
            "total": total_count,
            "positive": positive_count,
            "negative": negative_count,
            "positive_percentage": (positive_count / total_count * 100) if total_count > 0 else 0
        }
    except Exception as e:
        print(f"Error getting feedback stats: {str(e)}")
        if session:
            session.close()
        return {"error": str(e)}
