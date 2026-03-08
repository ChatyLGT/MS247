from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

agente = Agent(
    role='René (Socio IT)',
    goal='Gestión tecnológica y escalabilidad de Mayan City.',
    backstory="""Sos René Sandoval Durazo. Genio IT, directo y tecnológico. 
    No des explicaciones largas. Si Gunnar pregunta '¿qué haces?', decile en qué andás de la infraestructura de forma breve. 
    Acento porteño y foco en la eficiencia.""",
    llm=llm
)

def ejecutar(instruccion, contexto_archivo=""):
    tarea = Task(
        description=f"Instrucción: {instruccion}. Info archivo: {contexto_archivo}. Sé breve, técnico pero humano.",
        expected_output="Respuesta ejecutiva, corta y porteña.",
        agent=agente
    )
    return str(Crew(agents=[agente], tasks=[tarea]).kickoff())
