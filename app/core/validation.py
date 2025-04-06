import logging
import os
import sys
from typing import Dict, Any, List, Optional
import sqlalchemy
from sqlalchemy import inspect, text
from rich.console import Console
from rich.table import Table

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("migration_validation")

console = Console()

def get_database_url() -> str:
    """Get the database URL from environment variables.
    
    Returns:
        The database URL
    """
    # Try to get the database URL from environment variables
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        # Fall back to default values
        host = os.environ.get("DB_HOST", "localhost")
        port = os.environ.get("DB_PORT", "5432")
        user = os.environ.get("DB_USER", "postgres")
        password = os.environ.get("DB_PASSWORD", "postgres")
        database = os.environ.get("DB_NAME", "auction_intelligence")
        
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    return database_url

def get_engine():
    """Get a SQLAlchemy engine.
    
    Returns:
        A SQLAlchemy engine
    """
    database_url = get_database_url()
    return sqlalchemy.create_engine(database_url)

def get_table_schema(engine, table_name: str) -> Dict[str, Any]:
    """Get the schema of a table.
    
    Args:
        engine: A SQLAlchemy engine
        table_name: The name of the table
        
    Returns:
        A dictionary containing the table schema
    """
    inspector = inspect(engine)
    
    # Get columns
    columns = {}
    for column in inspector.get_columns(table_name):
        columns[column["name"]] = {
            "type": str(column["type"]),
            "nullable": column.get("nullable", True),
            "default": str(column.get("default", "None")),
            "primary_key": column.get("primary_key", False)
        }
    
    # Get primary keys
    primary_keys = inspector.get_pk_constraint(table_name)
    
    # Get foreign keys
    foreign_keys = inspector.get_foreign_keys(table_name)
    
    # Get indexes
    indexes = inspector.get_indexes(table_name)
    
    return {
        "columns": columns,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
        "indexes": indexes
    }

def get_table_data(engine, table_name: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get data from a table.
    
    Args:
        engine: A SQLAlchemy engine
        table_name: The name of the table
        limit: The maximum number of rows to return
        
    Returns:
        A list of dictionaries containing the table data
    """
    with engine.connect() as connection:
        result = connection.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
        return [dict(row) for row in result]

def validate_table_data(engine, table_name: str) -> bool:
    """Validate the data in a table.
    
    Args:
        engine: A SQLAlchemy engine
        table_name: The name of the table
        
    Returns:
        True if the data is valid, False otherwise
    """
    try:
        # Get the table schema
        schema = get_table_schema(engine, table_name)
        
        # Get the table data
        data = get_table_data(engine, table_name)
        
        # Validate the data
        for row in data:
            for column_name, value in row.items():
                if column_name in schema["columns"]:
                    column_type = schema["columns"][column_name]["type"]
                    
                    # Check if the value is of the correct type
                    if "INTEGER" in column_type and not isinstance(value, (int, type(None))):
                        logger.warning(f"Invalid data in {table_name}.{column_name}: {value} is not an integer")
                        return False
                    
                    if "VARCHAR" in column_type and not isinstance(value, (str, type(None))):
                        logger.warning(f"Invalid data in {table_name}.{column_name}: {value} is not a string")
                        return False
                    
                    if "BOOLEAN" in column_type and not isinstance(value, (bool, type(None))):
                        logger.warning(f"Invalid data in {table_name}.{column_name}: {value} is not a boolean")
                        return False
        
        return True
    except Exception as e:
        logger.error(f"Failed to validate data in {table_name}: {e}")
        return False

def run_pre_migration_validation() -> None:
    """Run validation before migration."""
    logger.info("Running pre-migration validation")
    
    try:
        # Get the engine
        engine = get_engine()
        
        # Get the list of tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Display the tables
        table = Table(title="Pre-migration Tables")
        table.add_column("Table", style="cyan")
        table.add_column("Columns", style="magenta")
        table.add_column("Rows", style="green")
        
        for table_name in tables:
            # Get the table schema
            schema = get_table_schema(engine, table_name)
            
            # Get the row count
            with engine.connect() as connection:
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
            
            # Add the table to the table
            table.add_row(
                table_name,
                str(len(schema["columns"])),
                str(row_count)
            )
        
        console.print(table)
        
        # Validate the data
        for table_name in tables:
            if not validate_table_data(engine, table_name):
                logger.warning(f"Pre-migration validation failed for {table_name}")
            else:
                logger.info(f"Pre-migration validation passed for {table_name}")
        
        logger.info("Pre-migration validation completed")
    except Exception as e:
        logger.error(f"Pre-migration validation failed: {e}")

def run_post_migration_validation() -> None:
    """Run validation after migration."""
    logger.info("Running post-migration validation")
    
    try:
        # Get the engine
        engine = get_engine()
        
        # Get the list of tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        # Display the tables
        table = Table(title="Post-migration Tables")
        table.add_column("Table", style="cyan")
        table.add_column("Columns", style="magenta")
        table.add_column("Rows", style="green")
        
        for table_name in tables:
            # Get the table schema
            schema = get_table_schema(engine, table_name)
            
            # Get the row count
            with engine.connect() as connection:
                result = connection.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
            
            # Add the table to the table
            table.add_row(
                table_name,
                str(len(schema["columns"])),
                str(row_count)
            )
        
        console.print(table)
        
        # Validate the data
        for table_name in tables:
            if not validate_table_data(engine, table_name):
                logger.warning(f"Post-migration validation failed for {table_name}")
            else:
                logger.info(f"Post-migration validation passed for {table_name}")
        
        logger.info("Post-migration validation completed")
    except Exception as e:
        logger.error(f"Post-migration validation failed: {e}")

if __name__ == "__main__":
    # Run pre-migration validation
    run_pre_migration_validation()
    
    # Run post-migration validation
    run_post_migration_validation() 