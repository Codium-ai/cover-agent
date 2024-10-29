import logging
import os

from jinja2 import Environment, StrictUndefined

from cover_agent.settings.config_loader import get_settings

MAX_TESTS_PER_RUN = 4

# Markdown text used as conditional appends
ADDITIONAL_INCLUDES_TEXT = """
## Additional Includes
The following is a set of included files used as context for the source code above. This is usually included libraries needed as context to write better tests:
======
{included_files}
======
"""

ADDITIONAL_INSTRUCTIONS_TEXT = """
## Additional Instructions
======
{additional_instructions}
======
"""

FAILED_TESTS_TEXT = """
## Previous Iterations Failed Tests
Below is a list of failed tests that you generated in previous iterations. Do not generate the same tests again, and take the failed tests into account when generating new tests.
======
{failed_test_runs}
======
"""


class PromptBuilder:
    def __init__(
        self,
        source_file_path: str,
        test_file_path: str,
        code_coverage_report: str,
        included_files: str = "",
        additional_instructions: str = "",
        failed_test_runs: str = "",
        language: str = "python",
        testing_framework: str = "NOT KNOWN",
    ):
        """
        The `PromptBuilder` class is responsible for building a formatted prompt string by replacing placeholders with the actual content of files read during initialization. It takes in various paths and settings as parameters and provides a method to generate the prompt.

        Attributes:
            prompt_template (str): The content of the prompt template file.
            source_file (str): The content of the source file.
            test_file (str): The content of the test file.
            code_coverage_report (str): The code coverage report.
            included_files (str): The formatted additional includes section.
            additional_instructions (str): The formatted additional instructions section.
            failed_test_runs (str): The formatted failed test runs section.
            language (str): The programming language of the source and test files.

        Methods:
            __init__(self, prompt_template_path: str, source_file_path: str, test_file_path: str, code_coverage_report: str, included_files: str = "", additional_instructions: str = "", failed_test_runs: str = "")
                Initializes the `PromptBuilder` object with the provided paths and settings.

            _read_file(self, file_path)
                Helper method to read the content of a file.

            build_prompt(self)
                Replaces placeholders with the actual content of files read during initialization and returns the formatted prompt string.
        """
        self.source_file_name = os.path.basename(source_file_path)
        self.test_file_name = os.path.basename(test_file_path)
        self.source_file = self._read_file(source_file_path)
        self.test_file = self._read_file(test_file_path)
        self.code_coverage_report = code_coverage_report
        self.language = language
        self.testing_framework = testing_framework

        # add line numbers to each line in 'source_file'. start from 1
        self.source_file_numbered = "\n".join(
            [f"{i + 1} {line}" for i, line in enumerate(self.source_file.split("\n"))]
        )
        self.test_file_numbered = "\n".join(
            [f"{i + 1} {line}" for i, line in enumerate(self.test_file.split("\n"))]
        )

        # Conditionally fill in optional sections
        self.included_files = (
            ADDITIONAL_INCLUDES_TEXT.format(included_files=included_files)
            if included_files
            else ""
        )
        self.additional_instructions = (
            ADDITIONAL_INSTRUCTIONS_TEXT.format(
                additional_instructions=additional_instructions
            )
            if additional_instructions
            else ""
        )
        self.failed_test_runs = (
            FAILED_TESTS_TEXT.format(failed_test_runs=failed_test_runs)
            if failed_test_runs
            else ""
        )

        self.stdout_from_run = ""
        self.stderr_from_run = ""

    def _read_file(self, file_path):
        """
        Helper method to read file contents.

        Parameters:
            file_path (str): Path to the file to be read.

        Returns:
            str: The content of the file.
        """
        try:
            with open(file_path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading {file_path}: {e}"

    def build_prompt(self) -> dict:
        variables = {
            "source_file_name": self.source_file_name,
            "test_file_name": self.test_file_name,
            "source_file_numbered": self.source_file_numbered,
            "test_file_numbered": self.test_file_numbered,
            "source_file": self.source_file,
            "test_file": self.test_file,
            "code_coverage_report": self.code_coverage_report,
            "additional_includes_section": self.included_files,
            "failed_tests_section": self.failed_test_runs,
            "additional_instructions_text": self.additional_instructions,
            "language": self.language,
            "max_tests": MAX_TESTS_PER_RUN,
            "testing_framework": self.testing_framework,
            "stdout": self.stdout_from_run,
            "stderr": self.stderr_from_run,
        }
        environment = Environment(undefined=StrictUndefined)
        try:
            system_prompt = environment.from_string(
                get_settings().test_generation_prompt.system
            ).render(variables)
            user_prompt = environment.from_string(
                get_settings().test_generation_prompt.user
            ).render(variables)
        except Exception as e:
            logging.error(f"Error rendering prompt: {e}")
            return {"system": "", "user": ""}

        # print(f"#### user_prompt:\n\n{user_prompt}")
        return {"system": system_prompt, "user": user_prompt}

    def build_prompt_custom(self, file) -> dict:
        """
        Builds a custom prompt by replacing placeholders with actual content from files and settings.

        Parameters:
            file (str): The file to retrieve settings for building the prompt.

        Returns:
            dict: A dictionary containing the system and user prompts.
        """
        variables = {
            "source_file_name": self.source_file_name,
            "test_file_name": self.test_file_name,
            "source_file_numbered": self.source_file_numbered,
            "test_file_numbered": self.test_file_numbered,
            "source_file": self.source_file,
            "test_file": self.test_file,
            "code_coverage_report": self.code_coverage_report,
            "additional_includes_section": self.included_files,
            "failed_tests_section": self.failed_test_runs,
            "additional_instructions_text": self.additional_instructions,
            "language": self.language,
            "max_tests": MAX_TESTS_PER_RUN,
            "testing_framework": self.testing_framework,
            "stdout": self.stdout_from_run,
            "stderr": self.stderr_from_run,
        }
        environment = Environment(undefined=StrictUndefined)
        try:
            settings = get_settings().get(file)
            if settings is None or not hasattr(settings, "system") or not hasattr(
                settings, "user"
            ):
                logging.error(f"Could not find settings for prompt file: {file}")
                return {"system": "", "user": ""}
            system_prompt = environment.from_string(settings.system).render(variables)
            user_prompt = environment.from_string(settings.user).render(variables)
        except Exception as e:
            logging.error(f"Error rendering prompt: {e}")
            return {"system": "", "user": ""}

        return {"system": system_prompt, "user": user_prompt}
