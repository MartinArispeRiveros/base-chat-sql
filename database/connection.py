from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from app.utils.config import load_config
import yaml
import json
import mysql.connector
load_dotenv() 

# def load_config():
#     with open("config.yaml", "r") as file:
#         config = yaml.safe_load(file)
#     return config

config = load_config()

# Database connection settings from config and .env
DB_USER = config["database"]["user"]
DB_PASS = config["database"]["password"]
DB_HOST = config["database"]["host"]
DB_PORT = config["database"]["port"]
DB_NAME = config["database"]["database_name"]
DB_DRIVER = config["database"]["driver"]
print('DB_HOST', DB_HOST)
# Create the connection URL
URL_DATABASE = f"{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy Engine
# engine = create_engine(
#     URL_DATABASE,
#     pool_pre_ping=True,  # Tests the connection before using it
#     pool_size=10,        # Maximum connections in the pool
#     max_overflow=5,      # Additional connections allowed beyond pool_size
#     echo=False           # Set to True for SQL debug logs
# )

db_config = {
    "host": DB_HOST, 
    "user": DB_USER,       
    "password":  DB_PASS,
    "database":  DB_NAME,
    "port": DB_PORT
}

engine = create_engine(URL_DATABASE)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        print(f"Database error occurred: {e}")
        db.rollback()
    finally:
        db.close()

def get_database_schema() -> str:
    connection = None
    try:
        connection = mysql.connector.connect(**get_db_config())

        cursor = connection.cursor(dictionary=True)
        
        # Retrieve All Tables
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = %s", (get_db_name(),))
        tables = cursor.fetchall()
        # Initialize the schema dictionary
        database_schema = {}

        # Retrieve Schema Information for Each Table
        for table in tables:
            table_name = table['TABLE_NAME']

            # Get column details for each table
            cursor.execute(f"""
                SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = %s AND TABLE_SCHEMA = %s
            """, (table_name, get_db_name()))
            columns = cursor.fetchall()

            # Get primary key information
            cursor.execute(f"""
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY' AND TABLE_SCHEMA = %s
            """, (table_name, get_db_name()))
            primary_keys = cursor.fetchall()

            # Organize the table schema
            database_schema[table_name] = {
                "columns": columns,
                "primary_keys": [key["COLUMN_NAME"] for key in primary_keys]
            }
        # Convert the Schema to JSON
        database_schema_json = json.dumps(database_schema, indent=4)
        return database_schema_json

    except mysql.connector.Error as e:
        print("Erro")
        return f"Error: {e}"
        

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def load_db_schema(db: Session = get_db):
    schema_dict = json.loads(get_database_schema())
    return {"schema": schema_dict}

def get_db_name():
    return db_config['database']

def get_db_config():
    return db_config