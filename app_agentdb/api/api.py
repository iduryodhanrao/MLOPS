from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app_agentdb.dbagent.dbagenttest import DBAgent
import asyncio

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace "*" with specific origins if needed
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize the DBAgent
agent = DBAgent(config_file="config.json", db_file="app_agentdb/db/sqllite/sample.db")


class TaskRequest(BaseModel):
    task_name: str


@app.post("/run-task/")
async def run_task(request: TaskRequest):
    """
    Run a specific task with the DBAgent and return the output.
    """
    try:
        # Run the task using the DBAgent
        await agent.run_session(request.task_name)

        # Collect the session history as the output
        output = agent.history

        # Return the output to the frontend
        return {"status": "success", "output": output}
    except Exception as e:
        return {"status": "error", "message": str(e)}