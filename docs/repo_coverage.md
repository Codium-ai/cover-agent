## Repo Coverage

New mode - scan an entire repo, auto identify the test files, auto collect context for each test file, and extend the test suite with new tests.
How to run:

1) Install cover-agent on your existing project venv: `pip install git+https://github.com/Codium-ai/cover-agent.git`
2) If your project doesn't have a `pyproject.toml` file, create one with:
```
[tool.poetry]
name = "cover-agent"
version = "0.0.0" # Placeholder
description = "Cover Agent Tool"
authors = ["QodoAI"]
license = "AGPL-3.0 license"
readme = "README.md"
```
3) Create a branch in your repo (we want to extend the tests on a dedicated branch)
4) cd to your repo root
5) Run the following command:
```shell

export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_REGION_NAME=...

poetry run cover-agent-full-repo \
  --project-language="python" \
  --project-root="<path_to_your_repo>" \
  --code-coverage-report-path="<path_to_your_repo>/coverage.xml" \
  --test-command="coverage run -m pytest <relative_path_to_unittest_folder> --cov=<path_to_your_repo> --cov-report=xml --cov-report=term" \
  --model=bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
```

Alternatively, if you dont want to use `poetry`, replace:

`poetry run cover-agent-full-repo`

with:

`python ./venv/lib/python3.10/site-packages/cover_agent/main_full_repo.py`
(Give the path to your actual installation)

Notes:
  - You can use other models, like 'gpt-4o' or 'o1-mini', but recommended to use 'sonnet-3.5' as this is currently the best code model in the world, and extending tests is a complex code task.

### Additional configuration options:

Additional configuration options:
- `--test-file` - If provided, the tool will extend the tests in this file only. Provide a relative path to the project root.
- `--test-folder` - If provided, the tool extend automatically only test files in this folder. Provide a relative path to the project root.
- `--max-test-files-allowed-to-analyze` - The maximum number of test files to analyze. Default is 20 (to avoid long running times).
- `--look-for-oldest-unchanged-test-files` - If set, the tool will sort the test files by the last modified date and analyze the oldest ones first. This is useful to find the test files that are most likely to be outdated, and for multiple runs. Default is False.
