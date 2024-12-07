from langchain.prompts import PromptTemplate

summarize_user_response_prompt = PromptTemplate(
    input_variables=["sql_query", "sql_result_str"],
    template=(
        """
        He ejecutado la siguiente consulta SQL:
        {sql_query}

        Los resultados obtenidos son los siguientes:
        {sql_result_str}

        Reformula esta información de forma que sea fácil de entender para un usuario no técnico.
        """
    )
)
