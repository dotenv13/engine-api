# Engine API (FastAPI)

Backend built with FastAPI.

## Requirements
- pip install -r requirements.txt

## Setup (local)

### 1) Create and activate venv
Windows (Git Bash):

python -m venv .venv
source .venv/Scripts/activate

    2) Install dependencies
pip install -r requirements.txt

    3) Environment variables
Create .env in project root

    4) Run the app
uvicorn app.main:app --reload


#Добавить все зависимости с проекта в requirements
pip freeze > requirements.txt


#Закоммитить:
git add .
git commit -m "message"
git push