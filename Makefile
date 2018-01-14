SOURCE_DIR=firefed/
TEST_CMD=pytest -v --cov ${SOURCE_DIR} --cov-report term-missing:skip-covered tests/

init:
	pip install pipenv --upgrade
	pipenv install --dev --skip-lock
test:
	pipenv run ${TEST_CMD}
testci:
	pipenv run ${TEST_CMD} -m "not unstable"
testq: # Run tests quickly (outside pipenv and without slow tests)
	${TEST_CMD} -m "not web and not unstable"
lint:
	pipenv run flake8
	pipenv run pylint --rcfile setup.cfg ${SOURCE_DIR}
codecov:
	pipenv run codecov
publish:
	rm -rf *.egg-info build/ dist/
	python setup.py bdist_wheel sdist
	twine upload -r pypi dist/*
	rm -rf *.egg-info build/ dist/
readme:
	python tools/make_readme.py
