import re
import json
from requests import Session
import nltk
from database.connection import load_db_schema
import sqlparse
from fastapi import HTTPException
from langchain_community.embeddings import OpenAIEmbeddings
from openai import AsyncOpenAI
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from app.streamlit.token_counter import add_tokens, get_total_tokens
from app.prompt_templates.sql_qa_prompt import sql_results_summary_prompt, translate_query_prompt, sql_query_prompt

nltk.download('stopwords')
    # def __init__(self, embeddings_model="openai", persist_directory="./vectorstore"):
        
    #     self.embeddings = OpenAIEmbeddings()
    #     self.vectorstore = Chroma(
    #         persist_directory=persist_directory,
    #         embedding_function=self.embeddings
    #     )
    #     self.persist_directory = persist_directory

def extract_relevant_schema(user_query: str, schema: dict) -> str:
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    schema_content = schema.get('schema', {})
    
    # Analyze the user's query
    parsed_query = sqlparse.parse(user_query)[0]
    tokens = [str(token).lower() for token in parsed_query.tokens if not token.is_whitespace]
    tokens = [word for token in tokens for word in token.split()] # Split tokens into individual words
    
    # Remove stop words from tokens
    filtered_tokens = [token for token in tokens if token not in stop_words]
    relevant_tables = set()
    
    # Lemmatize leaked tokens
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in filtered_tokens]
    print("Lemmatized Tokens:", lemmatized_tokens)

    # Find relevant tables in the schema
    for table_name in schema_content.keys():
        for token in lemmatized_tokens:
        # Compare table names and tokens
            if re.match(re.escape(table_name.lower()), token):
                relevant_tables.add(table_name)
            if re.sub(r's$', '', token) == re.sub(r's$', '', table_name.lower()):
                relevant_tables.add(table_name)
            elif re.sub(r'$', '', table_name.lower()) in token:
                relevant_tables.add(table_name)

    print("Relevant Tables Found:", relevant_tables)

    # Create a dictionary to filter tables and add related tables
    final_tables = {}
    for table_name in relevant_tables:
        if table_name not in final_tables:
            final_tables[table_name] = schema_content[table_name]

        # Check if there are foreign keys in the current table
        for column in schema_content[table_name].get('columns', []):
            column_name = column.get('COLUMN_NAME', '').lower()
            # If the column indicates a relationship, try adding the related table
            if column_name.endswith('_id'):
                related_table_name = column_name.rsplit('_', 1)[0]
                if related_table_name in schema_content:
                    final_tables[related_table_name] = schema_content[related_table_name]

                
    print("Final Relevant Tables:", final_tables.keys())

    # Create the subschema with the relevant tables
    sub_schema = {table: schema_content[table] for table in final_tables.keys()}

    return json.dumps(sub_schema, indent=4)

async def translate_query(user_query: str, model: str) -> str:

    glossary = {
        "cliente": "client",
        "usuario": "user",
        "ciudad": "city",
        "ciudades": "city",
        "pagos": "payment",
        "pago": "payment",
        "estado": "status",
        "reclamos": "claim",
        "reclamo" : "claim",
        "EN PROGRESO" : "EN PROGRESO",
        "en progreso" : "EN PROGRESO",
        "resuelto" : "RESUELTO",
        "RESUELTO" : "RESUELTO",
    }
    # Build the glossary instructions in the system message
    glossary_instructions = "\n".join([f'"{term}": "{translation}"' for term, translation in glossary.items()])

    # Create the system message with the glossary
    system_message = translate_query_prompt.format(glossary_instructions=glossary_instructions, user_query=user_query)

    # Call the translation model
    if model == "openai":
        print("DENTRO DEL TRANSLATE", user_query)
        translation = await _call_openai("gpt-4-turbo", system_message, user_query, query_type="translation")
        print("Traduccion:", translation)

    else:
        raise HTTPException(status_code=400, detail="Invalid model specified.")

    # Post-process the translation to ensure glossary consistency
    for term, translation_term in glossary.items():
        # Ensure exact glossary match (example. replace "cities" with "city" if it appears)
        translation = re.sub(rf'\b{re.escape(translation_term)}s\b', translation_term, translation, flags=re.IGNORECASE)
    print("Translation:", translation)
    return translation

async def get_sql_results_summary(sql_results: list, user_query: str, model: str) -> str:
    
    results_text = "\n".join([", ".join([f"{key}: {value}" for key, value in row.items()]) for row in sql_results])
    sql_results_summary_prompt_results= sql_results_summary_prompt.format(user_query=user_query, results_text=results_text)
    
    if not sql_results:
        return("No se encontraron resultados para tu consulta. Por favor, intenta con otros criterios o verifica tu consulta.")
    
    if model == "openai":
        return await _call_openai("gpt-4-turbo",sql_results_summary_prompt_results, user_query, query_type="summary")
    
    else:
        raise HTTPException(status_code=400, detail="Invalid model specified.")
    

async def _call_openai( model: str, system_message: str, user_query: str, query_type: str, has_user_query: bool = False) -> str:
    try:
        client = AsyncOpenAI()

        if has_user_query:
            messages_for_model = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_query}
            ]
        else:
            messages_for_model = [{"role": "system", "content": system_message}]

        response = await client.chat.completions.create(
            model=model,
            messages=messages_for_model
        )

        total_tokens = response.usage.total_tokens
        add_tokens(total_tokens) 
        prompt_tokens = response.usage.prompt_tokens
        completion_tokens = response.usage.completion_tokens
        
        print(f"Tokens del prompt (incluye schema): {prompt_tokens}")
        print(f"Tokens de la respuesta sql: {completion_tokens}")
        print(f"Tokens totales: {total_tokens}")
        print("TOKENS USADOS EN TOTAL", get_total_tokens())
        
        response_content = response.choices[0].message.content
        
        # response_json = json.loads(response_content)
        if query_type == "sql":
            return extract_sql_query(response_content)
        else:
            return response_content
            # return response_json.get("sparql_query")
    except json.JSONDecodeError as e:
        print("error3",e)
        raise HTTPException(status_code=500, detail="Error parsing the OpenAI response.")

def extract_sql_query(response_content: str) -> str:
    try:
        match = re.search(r'{.*}', response_content, re.DOTALL)
        
        if not match:
            raise HTTPException(status_code=500, detail="No JSON found in model response.")
        
        sql_query_json = match.group(0)
        response_json = json.loads(sql_query_json)
        sql_query = response_json.get("sql_query")
        
        if not sql_query:
            raise HTTPException(status_code=500, detail="No SQL query found in the response.")
        
        return sql_query
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error parsing the model response.")

async def generate_sql_query(user_query: str, db: Session, model: str) -> str:
    user_query_test = user_query
    full_schema = load_db_schema(db)

    translate_query_response = await translate_query(user_query_test, model)
    relevant_schema = extract_relevant_schema(translate_query_response, full_schema)
    print("Relevant Database Schema:", relevant_schema)
    
    system_message = sql_query_prompt.format(schema=relevant_schema)

    if model == "openai":
        return await _call_openai("gpt-4-turbo", system_message, translate_query_response, "sql", True)
    else:
        raise HTTPException(status_code=400, detail="Invalid model specified.")

    
    # async def _call_openai(system_message: str, open_ai_model: str) -> str:
    #     try:
    #         client = AsyncOpenAI()
    #         response = await client.chat.completions.create(
    #             model=open_ai_model,
    #             messages=[{"role": "system", "content": system_message}]
    #         )    
    #         total_tokens = response.usage.total_tokens
    #         add_tokens(total_tokens)
    #         print(f"Tokens totales de la traduccion: {total_tokens}")
    #         print("TOKENS USADOS EN TOTAL", get_total_tokens())
            
    #         return response.choices[0].message.content
            
    #     except Exception as e:
    #         print("error1", e)
    #         raise HTTPException(status_code=500, detail="Error generating translation response.")


        


    # async def _call_openai_for_response(system_message: str) -> str:
    #     try:
    #         client = AsyncOpenAI()
    #         response = await client.chat.completions.create(
    #             model="gpt-4-turbo",
    #             messages=[{"role": "system", "content": system_message}]
    #         )
    #         total_tokens = response.usage.total_tokens
    #         add_tokens(total_tokens)
    #         print(f"Tokens totales de verbalizacion: {total_tokens}")
    #         print("TOKENS USADOS EN TOTAL", get_total_tokens())
            
    #         return response.choices[0].message.content
            
        
    #     except Exception as e:
    #         print("error2", e)
    #         raise HTTPException(status_code=500, detail="Error generating human-readable response.")