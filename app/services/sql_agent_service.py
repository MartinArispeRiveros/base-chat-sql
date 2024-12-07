import warnings
from app.utils.config import load_config
from sqlalchemy.exc import SAWarning
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.chat_models import ChatOpenAI
from langchain_community.utilities.sql_database import SQLDatabase
from app.prompt_templates.agent_qa_prompt import summarize_user_response_prompt

config = load_config()
db = SQLDatabase.from_uri(config['database']['database_url'])  
llm = ChatOpenAI(temperature=0.2, model="gpt-3.5-turbo")

agent = create_sql_agent(
            llm=llm,
            toolkit=None,
            db=db,
            verbose=True,
            handle_parsing_errors=True,
        )

warnings.filterwarnings("ignore", category=SAWarning)
class AgentLLMService:
    def __init__(self, embeddings_model="openai", persist_directory="./vectorstore"):
        self.agent = agent

    def humanize_response(self, sql_query, sql_result):
        try:
            if sql_query.strip() == "SELECT 1;":
                return "La consulta no está diseñada para devolver datos útiles. Por favor, revisa la pregunta inicial."

            if isinstance(sql_result, list):
                sql_result_str = "\n".join(
                    [", ".join([f"{key}: {value}" for key, value in row.items()]) for row in sql_result]
                )
            else:
                sql_result_str = str(sql_result)

            prompt = summarize_user_response_prompt.format(
                sql_query=sql_query,
                sql_result_str=sql_result_str
            )

            humanized_response = llm.invoke([{"role": "system", "content": prompt}])
            return humanized_response
        except Exception as e:
            print(f"Error en humanize_response: {e}")
            return "No se pudo reformular el resultado."
        
    # Function to process queries with the agent
    def process_query_with_sql_agent(self, question):
        try:
            response = self.agent.run(question)
            print("Generated Response:", response)
            return response
        except Exception as e:
            print(f"Error en la ejecución del agente: {e}")
            return "Error al procesar la consulta."