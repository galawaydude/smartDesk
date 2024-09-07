import os
from openai import AzureOpenAI
from django.db import connection
from dotenv import load_dotenv

load_dotenv()

def get_azure_openai_client():
    return AzureOpenAI(
        azure_endpoint=os.getenv("PM_AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("PM_AZURE_OPENAI_API_KEY"),
        api_version="2024-05-01-preview"
    )

PM_DEPLOYMENT = os.getenv("PM_AZURE_OPENAI_DEPLOYMENT")

def get_schema():
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        schema = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table[0]});")
            columns = cursor.fetchall()
            schema.append(f"Table: {table[0]}\nColumns: {', '.join([f'{col[1]} {col[2]}' for col in columns])}")
    return "\n\n".join(schema)

def run_sql_query(query):
    with connection.cursor() as cursor:
        cursor.execute(query)
        result = cursor.fetchall()
    return result

def generate_sql_query(client, user_question, schema):
    prompt = f"""
Below is the table schema for a project management database:

{schema}

User question: {user_question}

Please provide an SQL query to answer the question. If the question requires data from multiple tables, use appropriate JOIN operations. Just give the SQL text without any explanations or formatting.
"""

    completion = client.chat.completions.create(
        model=PM_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are an SQL query generator for a project management database. Provide only the SQL query without any explanations. Use JOINs when necessary to work with multiple tables."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return completion.choices[0].message.content.strip()

def explain_results(client, user_question, schema, sql_query, query_result):
    prompt = f"""
The user asked about the project management system: "{user_question}"

The database schema is:
{schema}

The SQL query used to answer this question was:
{sql_query}

The result of this query was:
{query_result}

Please explain this result in natural language, as if you were a person answering the question about the project management system. Be concise but informative.
"""

    completion = client.chat.completions.create(
        model=PM_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "You are a helpful assistant that explains project management data based on database query results. Explain in natural language."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )
    return completion.choices[0].message.content.strip()

def project_management_chat(user_question):
    client = get_azure_openai_client()
    schema = get_schema()
    
    try:
        sql_query = generate_sql_query(client, user_question, schema)
        query_result = run_sql_query(sql_query)
        explanation = explain_results(client, user_question, schema, sql_query, query_result)
        return explanation
    except Exception as e:
        return f"An error occurred: {str(e)}. Please try again."