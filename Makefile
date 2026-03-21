SHELL = /bin/bash

ifeq ($(OS),Windows_NT)
        ACTIVATE := venv\Scripts\activate
    else
        ACTIVATE := source venv/bin/activate
    endif

.ONESHELL:
virtualenv:
	python3.11 -m venv venv
	@echo "Virtual environment created successfully"

install:
	$(ACTIVATE) && python -m pip install -r requirements.txt

update:
	$(ACTIVATE) && pip install --upgrade -r requirements.txt

initialize_git:
	git init
	git add .
	git commit -m "Initial commit"

initialize_dvc:
	$(ACTIVATE) && dvc init
	git add .
	git commit -m "Initialize DVC"

start_tracking:
	@echo "Start tracking MlFlow..."
	$(ACTIVATE) && mlflow server --host 127.0.0.1 --port 8080 --backend-store-uri src/models/mlruns

start_QA:
	@echo "Start Quality Assurance checks..."
	$(ACTIVATE) && echo "Executing Ruff..." && ruff check .
	$(ACTIVATE) && echo "Executing Mypy..." && mypy src
	$(ACTIVATE) && echo "Executing Bandit..." && bandit -r src

start_testing:
	@echo "Start testing..."
	pytest test/
