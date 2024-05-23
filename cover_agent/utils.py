import logging
import re
from typing import List

import yaml


def load_yaml(response_text: str, keys_fix_yaml: List[str] = []) -> dict:
    response_text = response_text.removeprefix("```yaml").rstrip("`")
    try:
        data = yaml.safe_load(response_text)
    except Exception as e:
        logging.error(f"Failed to parse AI prediction: {e}")
        data = try_fix_yaml(response_text, keys_fix_yaml=keys_fix_yaml)
    return data


def try_fix_yaml(response_text: str, keys_fix_yaml: List[str] = []) -> dict:
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
        logging.info(f"Failed to parse AI prediction after adding |-\n")

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
            logging.info(f"Successfully parsed AI prediction after removing {i} lines")
            return data
        except:
            pass
