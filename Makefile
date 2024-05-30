# Makefile

.PHONY: test build installer

# Run unit tests with Pytest
test:
	poetry run pytest --junitxml=testLog.xml --cov=cover_agent --cov-report=xml:cobertura.xml --cov-report=term --cov-fail-under=70 --log-cli-level=INFO

# Use Python Black to format python files
format:
	black .

# Generate wheel file using poetry build command
build:
	poetry build

# Build an executable using Pyinstaller
installer:
	poetry run pyinstaller \
		--add-data "cover_agent/version.txt:." \
		--add-data "cover_agent/settings/language_extensions.toml:." \
		--add-data "cover_agent/settings/test_generation_prompt.toml:." \
		--add-data "cover_agent/settings/analyze_suite_test_headers_indentation.toml:." \
		--add-data "cover_agent/settings/analyze_suite_test_insert_line.toml:." \
		--hidden-import=tiktoken_ext.openai_public \
		--hidden-import=tiktoken_ext \
		--onefile \
		--name cover-agent \
		cover_agent/main.py
