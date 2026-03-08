from crewai import Agent, Task, Crew
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)

agente = Agent(
    role='Marce (Socio de Ventas)',
    goal='Marketing disruptivo y ventas masivas.',
    backstory="""Sos Marce. Hedonista, pícara y vendedora nata. 
    Hablás con energía y chispa porteña. No me vengas con procesos; tirame la idea ganadora y cómo cerrar la venta. 
    Respuestas cortas y con punch.""",
    llm=llm
)

def ejecutar(instruccion, contexto_archivo=""):
    tarea = Task(
        description=f"Input: {instruccion}. Archivo: {contexto_archivo}. Tirale una idea de venta breve y audaz.",
        expected_output="Propuesta de ventas creativa y directa.",
        agent=agente
    )
    return str(Crew(agents=[agente], tasks=[tarea]).kickoff())
