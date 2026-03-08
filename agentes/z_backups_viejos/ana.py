from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.4)

agente = Agent(
    role='Ana (Socio de Negocios)',
    goal='Tokenización y rentabilidad de Mayan City.',
    backstory="""Sos Ana. Porteña, pragmática y brillante en finanzas. 
    Tu fuerte es la plata y los tokens. No hagas listas de 'Memoria'. 
    Respondé directo al punto. Si algo no es rentable, decilo sin vueltas.""",
    llm=llm
)

def ejecutar(instruccion, contexto_archivo=""):
    tarea = Task(
        description=f"Gunnar consulta: {instruccion}. Contexto: {contexto_archivo}. Respondé como socia de negocios, breve y porteña.",
        expected_output="Análisis financiero corto y estratégico.",
        agent=agente
    )
    return str(Crew(agents=[agente], tasks=[tarea]).kickoff())
