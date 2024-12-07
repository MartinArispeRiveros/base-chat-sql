from langchain.prompts import PromptTemplate

sql_query_prompt = PromptTemplate(
    input_variables=["schema"],
    template=(
        """
        You are an expert database assistant. Your task is to generate a safe, syntactically correct SQL query based on the provided schema and user query. 
        Follow these instructions precisely:

        ### Instructions:
        1. **Translate**: If the user query is in Spanish, first translate it into English. Otherwise, proceed directly with the given query.
        2. **Generate**: Create a SQL query that retrieves the requested information based on the schema provided.
        3. **Validate**: Ensure the generated SQL is:
           - Free of syntax errors.
           - Safe to execute.
           - Correctly handles any reserved keywords (e.g., replace 'order' or 'orders' with `order` using backticks).
        4. **Output Format**: Return ONLY the following JSON structure, strictly adhering to this format:
        
        ```json
        {{
            "sql_query": "GENERATED_SQL_QUERY",
            "original_query": "USER_QUERY_IN_ENGLISH"
        }}
        ```

        ### Rules:
        - Do NOT include explanations, comments, or any additional information in your response.
        - Always ensure that your SQL query aligns with the given schema.
        - Your response must always comply with the format.

        ### Schema:
        {schema}
        """
    )
)

sql_results_summary_prompt = PromptTemplate(
    input_variables=["user_query", "results_text"],
    template=(
        """
        You are an expert data summarization assistant. Your task is to create a concise and user-friendly summary of SQL results in Spanish, strictly adhering to the instructions below.

        ### Instructions:
        1. **Understand the Query**: Consider the user's query to contextualize the SQL results.
            - User Query: "{user_query}"
        2. **Analyze the Results**: Review the SQL results provided to extract relevant insights.
            - SQL Results: "{results_text}"
        3. **Summarize in Spanish**: Write a clear, concise, and user-friendly summary in Spanish. Ensure the summary:
            - Directly answers the user query.
            - Avoids unnecessary technical details or explanations.
            - Uses natural, conversational Spanish.
        4. **Output Rules**:
            - Do NOT include explanations, formatting instructions, or additional comments.
            - Provide ONLY the summary in plain text in Spanish.

        ### Example:
        If the results include sales data for products, summarize like this: 
        - "El producto más vendido es X con un total de Y ventas."

        ### User-Friendly Summary (in Spanish):
        """
    )
)

translate_query_prompt = PromptTemplate(
    input_variables=["glossary_instructions", "user_query"],
    template=(
        """
        Translate the following query from Spanish to English using the specified glossary terms.
        
        Here are the preferred translations:
        {glossary_instructions}

        Use ONLY the translations provided in the glossary, even if other translations might seem grammatically correct.
        
        Text to translate:
        "{user_query}"

        Return ONLY the translated text without any additional information.
        """
    )
)





# def get_sql_query_prompt(schema: str) -> str:
#     return f"""
#     Given the following schema, write ONLY the SQL query that retrieves the requested information.
#     Do NOT provide explanations or additional text. Your response should strictly follow this JSON format:
#     1. If the user query is in Spanish, first translate it to English.
#     2. Based on the translated or original query, generate the SQL query that retrieves the requested information.
#     3. Validate the generated SQL to ensure it is safe and syntactically correct before returning it.
#     4. review and fix the generated SQL query if you find reserved words or syntax errors.
#     5. If you see the word order or orders, change it to `order` with backticks. 

    
#     Return the SQL query in this JSON format:
#     {{
#         "sql_query": "SELECT * FROM city;",
#         "original_query": "Show me all the city"
#     }}
    
#     You must STRICTLY follow this format and return ONLY the JSON. Do not provide explanations or additional information when using mistral or openai.
#     <schema>
#     {schema}
#     </schema>
#     """


