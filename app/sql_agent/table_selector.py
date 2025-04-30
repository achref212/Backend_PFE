def select_relevant_tables(prompt: str, schema: dict) -> list:
    keywords = prompt.lower().split()
    relevant_tables = []

    for table, columns in schema.items():
        for col in columns:
            if any(k in col.lower() or k in table.lower() for k in keywords):
                relevant_tables.append(table)
                break
    return relevant_tables