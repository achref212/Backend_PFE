from app.sql_agent import schema_reader, table_selector, sql_generator, sql_executor, result_summarizer, query_analyzer


def run_sql_agent(prompt: str):
    if not query_analyzer.detect_sql_intent(prompt):
        return "❌ Ce prompt ne semble pas adapté à une requête SQL."

    schema = schema_reader.get_schema_overview()
    tables = table_selector.select_relevant_tables(prompt, schema)
    query = sql_generator.generate_sql_query(prompt, schema, tables)
    result = sql_executor.execute_sql(query)
    summary = result_summarizer.summarize_result(result, prompt)

    return {
        "sql_query": query,
        "raw_result": result,
        "summary": summary
    }