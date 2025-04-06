from pprint import pformat
import matplotlib.pyplot as plt
from google import genai
from google.genai import types
import sqlite3
import asyncio
import json

with open("../../config.json", "r") as config_file:
    config = json.load(config_file)
    GOOGLE_API_KEY = config.get("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY is not set in config.json.")
    
#connect to sqllite
db_file = "../db/sqllite/sample.db"
db_conn = sqlite3.connect(db_file)


def execute_query(sql: str) -> list[list[str]]:
    """Execute an SQL statement, returning the results."""
    print(f' - DB CALL: execute_query({sql})')

    cursor = db_conn.cursor()

    cursor.execute(sql)
    return cursor.fetchall()

async def handle_response(stream, tool_impl=None):
  """Stream output and handle any tool calls during the session."""
  all_responses = []

  async for msg in stream.receive():
    all_responses.append(msg)

    if text := msg.text:
      # Output any text chunks that are streamed back.
      if len(all_responses) < 2 or not all_responses[-2].text:
        # Display a header if this is the first text chunk.
        print('### Text')

      print(text, end='')

    elif tool_call := msg.tool_call:
      # Handle tool-call requests.
      for fc in tool_call.function_calls:
        print('### Tool call')

        # Execute the tool and collect the result to return to the model.
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
      # Print any messages showing code the model generated and ran.

      for part in msg.server_content.model_turn.parts:
          if code := part.executable_code:
            print(f'### Code\n```\n{code.code}\n```')

          elif result := part.code_execution_result:
            print(f'### Result: {result.outcome}\n'
                  f'```\n{pformat(result.output)}\n```')

          elif img := part.inline_data:
            # Save the image data to a file and display it using matplotlib
            img_file = "../static/output_image.png"
            with open(img_file, "wb") as f:
                f.write(img.data)
            img_data = plt.imread(img_file)
            plt.imshow(img_data)
            plt.axis('off')
            plt.show()

  print()
  return all_responses

model = 'gemini-2.0-flash-exp'
live_client = genai.Client(api_key=GOOGLE_API_KEY,
                           http_options=types.HttpOptions(api_version='v1alpha'))

# Wrap the existing execute_query tool you used in the earlier example.
execute_query_tool_def = types.FunctionDeclaration.from_callable(
    client=live_client, callable=execute_query)

# Provide the model with enough information to use the tool, such as describing
# the database so it understands which SQL syntax to use.
sys_int = """You are a database interface. Use the `execute_query` function
to answer the users questions by looking up information in the database,
running any necessary queries and responding to the user.

You need to look up table schema using sqlite3 syntax SQL, then once an
answer is found be sure to tell the user. If the user is requesting an
action, you must also execute the actions.
"""

config = {
    "response_modalities": ["TEXT"],
    "system_instruction": {"parts": [{"text": sys_int}]},
    "tools": [
        {"code_execution": {}},
        {"function_declarations": [execute_query_tool_def.to_json_dict()]},
    ],
}

async def main():

    async with live_client.aio.live.connect(model=model, config=config) as session:

        message = "Please generate and insert 5 new rows in the orders table."
        print(f"> {message}\n")

        await session.send(input=message, end_of_turn=True)
        await handle_response(session, tool_impl=execute_query)

    async with live_client.aio.live.connect(model=model, config=config) as session:

        message = "Can you figure out the number of orders that were made by each of the staff?"

        print(f"> {message}\n")
        await session.send(input=message, end_of_turn=True)
        await handle_response(session, tool_impl=execute_query)

        message = "Generate and run some code to plot this as a python seaborn chart"

        print(f"> {message}\n")
        await session.send(input=message, end_of_turn=True)
        await handle_response(session, tool_impl=execute_query)

asyncio.run(main())