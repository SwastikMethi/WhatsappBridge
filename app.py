from fastapi import FastAPI
from pydantic import BaseModel, Field
from agents.claude import ClaudeService

app = FastAPI()
claude = ClaudeService()
class Command(BaseModel):
    text: str = Field(min_length=1, max_length=4000)

@app.post("/command")
async def execute_command(command: Command):
    # Here you can add the logic to execute the command
    response = await claude.reply(command.text)
    return {"reply": response}