import argparse
import logging
import os
import re
import yaml

from typing import List

from grep_ast import filename_to_lang

from cover_agent.lsp_logic.utils.utils import is_forbidden_directory
from cover_agent.version import __version__


def load_yaml(response_text: str, keys_fix_yaml: List[str] = []) -> dict:
    """
    Load and parse YAML data from a given response text.

    Parameters:
    response_text (str): The response text containing YAML data.
    keys_fix_yaml (List[str]): A list of keys to fix YAML formatting (default is an empty list).

    Returns:
    dict: The parsed YAML data.

    If parsing the YAML data directly fails, it attempts to fix the YAML formatting using the 'try_fix_yaml' function.

    Example:
        load_yaml(response_text, keys_fix_yaml=['key1', 'key2'])

    """
    response_text = response_text.strip().removeprefix("```yaml").rstrip("`")
    try:
        data = yaml.safe_load(response_text)
    except Exception as e:
        logging.info(
            f"Failed to parse AI prediction: {e}. Attempting to fix YAML formatting."
        )
        data = try_fix_yaml(response_text, keys_fix_yaml=keys_fix_yaml)
        if not data:
            logging.info(f"Failed to parse AI prediction after fixing YAML formatting.")
    return data


def try_fix_yaml(response_text: str, keys_fix_yaml: List[str] = []) -> dict:
    """
    Attempt to fix YAML formatting issues in the given response text.

    Parameters:
    response_text (str): The response text that may contain YAML data with formatting issues.
    keys_fix_yaml (List[str]): A list of keys to fix YAML formatting (default is an empty list).

    Returns:
    dict: The parsed YAML data after attempting to fix formatting issues.

    The function tries multiple fallback strategies to fix YAML formatting issues:
    1. Tries to convert lines containing specific keys to multiline format.
    2. Tries to extract YAML snippet enclosed between ```yaml``` tags.
    3. Tries to remove leading and trailing curly brackets.
    4. Tries to remove last lines iteratively to fix the formatting.

    If none of the strategies succeed, an empty dictionary is returned.

    Example:
        try_fix_yaml(response_text, keys_fix_yaml=['key1', 'key2'])
    """
    response_text_lines = response_text.split("\n")

    # first fallback - try to convert 'relevant line: ...' to relevant line: |-\n        ...'
    response_text_lines_copy = response_text_lines.copy()
    for i in range(0, len(response_text_lines_copy)):
        for key in keys_fix_yaml:
            if (
                key in response_text_lines_copy[i]
                and not "|-" in response_text_lines_copy[i]
            ):
                response_text_lines_copy[i] = response_text_lines_copy[i].replace(
                    f"{key}", f"{key} |-\n        "
                )
    try:
        data = yaml.safe_load("\n".join(response_text_lines_copy))
        logging.info(f"Successfully parsed AI prediction after adding |-\n")
        return data
    except:
        pass

    # second fallback - try to extract only range from first ```yaml to ````
    snippet_pattern = r"```(yaml)?[\s\S]*?```"
    snippet = re.search(snippet_pattern, "\n".join(response_text_lines_copy))
    if snippet:
        snippet_text = snippet.group()
        try:
            data = yaml.safe_load(snippet_text.removeprefix("```yaml").rstrip("`"))
            logging.info(
                f"Successfully parsed AI prediction after extracting yaml snippet"
            )
            return data
        except:
            pass

    # third fallback - try to remove leading and trailing curly brackets
    response_text_copy = (
        response_text.strip().rstrip().removeprefix("{").removesuffix("}").rstrip(":\n")
    )
    try:
        data = yaml.safe_load(response_text_copy)
        logging.info(f"Successfully parsed AI prediction after removing curly brackets")
        return data
    except:
        pass

    # fourth fallback - try to remove last lines
    data = {}
    for i in range(1, len(response_text_lines)):
        response_text_lines_tmp = "\n".join(response_text_lines[:-i])
        try:
            data = yaml.safe_load(response_text_lines_tmp)
            if "language" in data:
                logging.info(
                    f"Successfully parsed AI prediction after removing {i} lines"
                )
                return data
        except:
            pass

    ## fifth fallback - brute force:
    ## detect 'language:' key and use it as a starting point.
    ## look for last '\n\n' after last 'test_code:' and extract the yaml between them
    try:
        # (1) find index of '\nlanguage:' string:
        index_start = response_text.find("\nlanguage:")
        if index_start == -1:
            index_start = response_text.find(
                "language:"
            )  # if response starts with 'language:'
        # (2) find last appearance ot 'test_code:' string:
        index_last_code = response_text.rfind("test_code:")
        # (3) find the first place after 'test_code:' where there is a '\n\n' character:
        index_end = response_text.find("\n\n", index_last_code)
        if index_end == -1:
            index_end = len(response_text)  # response ends with valid yaml
        response_text_copy = response_text[index_start:index_end].strip()
        try:
            data = yaml.safe_load(response_text_copy)
            logging.info(
                f"Successfully parsed AI prediction when using the language: key as a starting point"
            )
            return data
        except:
            pass
    except:
        pass


def parse_args_full_repo():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description=f"Cover Agent v{__version__}")
    parser.add_argument(
        "--max-test-files-allowed-to-analyze", type=int, default=20, help="The maximum number of test files to analyze."
    )
    parser.add_argument("--look-for-oldest-unchanged-test-file",
                        action="store_true", help="If set, Cover-Agent will look for the oldest unchanged test file to analyze.")

    parser.add_argument(
        "--project-language", required=True, default="python", help="The programming language of the project ([python, javascript, typescript])."
    )
    parser.add_argument(
        "--project-root", required=True, help="Path to the root of the project."
    )

    parser.add_argument(
        "--run-each-test-separately",
        type=bool,
        default=True,
        help="Run each test separately. Default: True"
    )

    # ToDo
    # parser.add_argument(
    #     "--unittest-folder-rel-path", required=False, help="Relative path to the unittest folder."
    # )

    parser.add_argument(
        "--code-coverage-report-path",
        required=True,
        help="Path to the code coverage report file.",
    )
    parser.add_argument(
        "--test-command",
        required=True,
        help="The command to run tests and generate coverage report.",
    )
    parser.add_argument(
        "--test-command-dir",
        default=os.getcwd(),
        help="The directory to run the test command in. Default: %(default)s.",
    )
    parser.add_argument(
        "--coverage-type",
        default="cobertura",
        help="Type of coverage report. Default: %(default)s.",
    )
    parser.add_argument(
        "--report-filepath",
        default="test_results.html",
        help="Path to the output report file. Default: %(default)s.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=3,
        help="The maximum number of iterations. Default: %(default)s.",
    )
    parser.add_argument(
        "--additional-instructions",
        default="",
        help="Any additional instructions you wish to append at the end of the prompt. Default: %(default)s.",
    )
    parser.add_argument(
        "--model",
        default="bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0",
        help="Which LLM model to use. Default: %(default)s.",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:11434",
        help="The API url to use for Ollama or Hugging Face. Default: %(default)s.",
    )
    parser.add_argument(
        "--strict-coverage",
        action="store_true",
        help="If set, Cover-Agent will return a non-zero exit code if the desired code coverage is not achieved. Default: False.",
    )
    parser.add_argument(
        "--run-tests-multiple-times",
        type=int,
        default=1,
        help="Number of times to run the tests generated by Cover Agent. Default: %(default)s.",
    )
    parser.add_argument(
        "--use-report-coverage-feature-flag",
        action="store_true",
        help="Setting this to True considers the coverage of all the files in the coverage report. This means we consider a test as good if it increases coverage for a different file other than the source file. Default: False.",
    )
    parser.add_argument(
        "--log-db-path",
        default="",
        help="Path to optional log database. Default: %(default)s.",
    )
    parser.add_argument(
        "--test-file-output-path",
        required=False,
        help="Path to the output test file.",
        default="",
        type=str,
    )
    parser.add_argument(
        "--desired-coverage",
        type=int,
        default=100,
        help="The desired coverage percentage. Default: %(default)s.",
    )
    parser.add_argument(
        "--diff-coverage",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--branch",
        type=str,
        default="main",
    )
    return parser.parse_args()


def find_test_files(args) -> list:
    """
    Scan the project directory for test files.
    """
    project_dir = args.project_root
    language = args.project_language
    MAX_TEST_FILES = args.max_test_files_allowed_to_analyze
    test_files = []
    for root, dirs, files in os.walk(project_dir):
        # Check if the current directory is a 'test' directory
        if not is_forbidden_directory(root.__add__(os.sep), language):
            if 'test' in root.split(os.sep):
                for file in files:
                    if filename_to_lang(file) == language:
                        test_files.append(os.path.join(root, file))
            else:
                # Check if any file contains 'test' in its name
                for file in files:
                    if 'test' in file:
                        if filename_to_lang(file) == language:
                            test_files.append(os.path.join(root, file))
        if len(test_files) >= MAX_TEST_FILES and args.look_for_oldest_unchanged_test_file:
            print(f"Found {len(test_files)} test files. Stopping at {MAX_TEST_FILES} test files.")
            break

    if args.look_for_oldest_unchanged_test_file:
        test_files.sort(key=os.path.getmtime)
        test_files = test_files[:MAX_TEST_FILES]

    return test_files
