from pprint import pformat
import matplotlib.pyplot as plt
from google import genai
from google.genai import types
import sqlite3
import asyncio
import json


class DBAgent:
    def __init__(self, config_file: str, db_file: str):
        self.config = self.load_config(config_file)
        self.google_api_key = self.config.get("GOOGLE_API_KEY")
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY is not set in the config file.")
        self.db_conn = sqlite3.connect(db_file)
        self.model = 'gemini-2.0-flash-exp'
        self.live_client = genai.Client(
            api_key=self.google_api_key,
            http_options=types.HttpOptions(api_version='v1alpha')
        )
        self.config = self.create_model_config()

    @staticmethod
    def load_config(config_file: str) -> dict:
        """Load configuration from a JSON file."""
        with open(config_file, "r") as file:
            return json.load(file)

    def execute_query(self, sql: str) -> list[list[str]]:
        """Execute an SQL statement and return the results."""
        print(f' - DB CALL: execute_query({sql})')
        cursor = self.db_conn.cursor()
        cursor.execute(sql)
        return cursor.fetchall()

    def create_model_config(self) -> dict:
        """Create the configuration for the model."""
        sys_int = """You are a database interface. Use the `execute_query` function
        to answer the user's questions by looking up information in the database,
        running any necessary queries, and responding to the user.

        You need to look up table schema using sqlite3 syntax SQL, then once an
        answer is found be sure to tell the user. If the user is requesting an
        action, you must also execute the actions.
        """
        execute_query_tool_def = types.FunctionDeclaration.from_callable(
            client=self.live_client, callable=self.execute_query
        )
        return {
            "response_modalities": ["TEXT"],
            "system_instruction": {"parts": [{"text": sys_int}]},
            "tools": [
                {"code_execution": {}},
                {"function_declarations": [execute_query_tool_def.to_json_dict()]},
            ],
        }

    async def handle_response(self, stream, tool_impl=None):
        """Stream output and handle any tool calls during the session."""
        all_responses = []

        async for msg in stream.receive():
            all_responses.append(msg)

            if text := msg.text:
                if len(all_responses) < 2 or not all_responses[-2].text:
                    print('### Text')
                print(text, end='')

            elif tool_call := msg.tool_call:
                for fc in tool_call.function_calls:
                    print('### Tool call')
                    if callable(tool_impl):
                        try:
                            result = tool_impl(**fc.args)
                        except Exception as e:
                            result = str(e)
                    else:
                        result = 'ok'

                    tool_response = types.LiveClientToolResponse(
                        function_responses=[types.FunctionResponse(
                            name=fc.name,
                            id=fc.id,
                            response={'result': result},
                        )]
                    )
                    await stream.send(input=tool_response)

            elif msg.server_content and msg.server_content.model_turn:
                for part in msg.server_content.model_turn.parts:
                    if code := part.executable_code:
                        print(f'### Code\n```\n{code.code}\n```')
                    elif result := part.code_execution_result:
                        print(f'### Result: {result.outcome}\n'
                              f'```\n{pformat(result.output)}\n```')
                    elif img := part.inline_data:
                        img_file = "../static/output_image.png"
                        with open(img_file, "wb") as f:
                            f.write(img.data)
                        img_data = plt.imread(img_file)
                        plt.imshow(img_data)
                        plt.axis('off')
                        plt.show()

        print()
        return all_responses

    async def run_session(self, message: str):
        """Run a session with the live client."""
        async with self.live_client.aio.live.connect(model=self.model, config=self.config) as session:
            print(f"> {message}\n")
            await session.send(input=message, end_of_turn=True)
            await self.handle_response(session, tool_impl=self.execute_query)

    async def main(self):
        """Main entry point for the DBAgent."""
        #await self.run_session("Please delete all rows in the orders table.")
        await self.run_session("Please generate and insert 5 new rows in the orders table.")
        await self.run_session("Can you figure out the number of orders that were made by each of the staff?")
        await self.run_session("Generate plot for number of orders made by each staff as a python seaborn chart.")


if __name__ == "__main__":
    agent = DBAgent(config_file="../../config.json", db_file="../db/sqllite/sample.db")
    asyncio.run(agent.main())