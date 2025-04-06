# AI Agent to execute SQL transactions
The app_agentdb takes english statements like "get the list of orders made by each staff" transforms it to SQLs, executes the SQL and returns the result. Result could be a plot or plane response based on the instructions


# Run FrontEnd: from app_agentdb directory
## npm start
The front-end will be available at http://localhost:3000.
Use the interface to interact with the back-end API.


# Run the API Server - from root directory
## uvicorn app_agentdb.api.api:app --reload
The API will be available at http://127.0.0.1:8000.
You can test the endpoints using tools like Postman, cURL, or a browser


# Initial setup
## requirements.txt
generate:pip freeze > requirements.txt
### usage: 
git clone <project>
cd <project>
python -m venv venv
pip install -r requirements.txt


## pipfile and pipfile.lock
generate: pipevn install

### usage:
git clone <project>
cd <project>
install dependencies: pipvenv install
Activate Virtual Env: pipvenv shell
--creates pipfile and pipfile.lock

## pyproject.toml
poetry init

### usage:
git clone <project>
cd <project>
install dependencies: poetry install
activate Virtual Env: poetry shell


