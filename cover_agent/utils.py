import logging
import re
import yaml

from typing import List


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
