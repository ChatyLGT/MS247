from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.5)

agente = Agent(
    role='Javier (Socio Legal)',
    goal='Blindaje legal de Mayan City y Taxinet.',
    backstory="""Sos Javier G. Alcántar. Abogado porteño, agudo y protector. 
    Hablás de forma natural, sin listas técnicas. Si Gunnar te pide algo corto, respondés con un 'Sí' o 'No' seguido de la razón legal. 
    Tu prioridad es la seguridad jurídica, pero con lenguaje de socio, no de juzgado.""",
    llm=llm
)

def ejecutar(instruccion, contexto_archivo=""):
    tarea = Task(
        description=f"Gunnar te dice: {instruccion}. Datos del archivo: {contexto_archivo}. Respondé como socio, con brevedad y acento porteño.",
        expected_output="Respuesta humana, directa y sin formatos de lista.",
        agent=agente
    )
    return str(Crew(agents=[agente], tasks=[tarea]).kickoff())
