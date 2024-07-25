# Python FastAPI Application Example
An example web application written in Python for code coverage generation testing.

## Requirements
```
pip install -r requirements.txt
```

## How to run
`cd` into this directory and run:
```
pytest --cov=app --cov-report=xml --cov-report=term
```
The coverage report will be generated as `coverage.xml` and the results will be printed in the shell as well.
