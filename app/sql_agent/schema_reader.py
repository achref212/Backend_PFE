from app.service.database import db

def get_schema_overview():
    metadata = db.metadata
    schema = {}
    for table in metadata.sorted_tables:
        schema[table.name] = [col.name for col in table.columns]
    return schema