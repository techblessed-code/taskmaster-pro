
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Secret key for forms and session security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Upload folder path
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

    # Maximum file upload size (16MB)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
