test:
	pipenv run pytest firefed/

lint:
	pipenv run pylint .

format:
	pipenv run yapf -r -i .
