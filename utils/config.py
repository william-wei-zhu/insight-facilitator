import os

# Application base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Determine database path based on environment
def get_db_path():
    """Get the appropriate database path based on environment"""
    # Use data folder for all environments for consistency
    data_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)  # Ensure directory exists
    
    # For Hugging Face Spaces and other cloud environments, use absolute /data path
    if "SPACE_ID" in os.environ or "AWS_REGION" in os.environ or "GOOGLE_CLOUD_PROJECT" in os.environ:
        os.makedirs("/data", exist_ok=True)  # Ensure directory exists
        return "/data/feedback.db"  # Persistent path
    else:
        # For local development, use the project's data folder
        return os.path.join(data_dir, 'feedback.db')

# Database path that all modules should use
DB_PATH = get_db_path()
