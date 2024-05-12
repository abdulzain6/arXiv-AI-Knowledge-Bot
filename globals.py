from peewee import SqliteDatabase
from data_storage import PDFFileManager, ChatManager
from pinecone_client import initialize_pinecone
from utils import load_config, load_credentials

db = SqliteDatabase('database/names.db')
monitor_interval = 30
channel_name = "general"
chosen_pdf_name = ""
database_manager = PDFFileManager(db = db)
chat_manager = ChatManager(db = db)
creds = load_credentials()
config = load_config()
initialize_pinecone(creds["PINECONE_API_KEY"], creds["PINECONE_ENVIRONMENT"])
