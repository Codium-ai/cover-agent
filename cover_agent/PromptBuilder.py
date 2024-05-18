# Markdown text used as conditional appends
ADDITIONAL_INCLUDES_TEXT = """
## Additional Includes
The following is a set of included files used as context for the source code above. This is usually included libraries needed as context to write better tests:
```
{included_files}
```
"""

ADDITIONAL_INSTRUCTIONS_TEXT = """
## Additional Instructions
__Remember, DO NOT REPEAT__ previously failed tests.
{additional_instructions}
"""

FAILED_TESTS_TEXT = """
## Previous Iterations Failed Tests
Below is a list of failed tests that you generated in previous iterations, if available. Very important - __Do not generate these same tests again__:
```
{failed_test_runs}
```
"""
class PromptBuilder:

    def __init__(
        self,
        prompt_template_path: str,
        source_file_path: str,
        test_file_path: str,
        code_coverage_report: str,
        included_files: str = "",
        additional_instructions: str = "",
        failed_test_runs: str = "",
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

        Methods:
            __init__(self, prompt_template_path: str, source_file_path: str, test_file_path: str, code_coverage_report: str, included_files: str = "", additional_instructions: str = "", failed_test_runs: str = "")
                Initializes the `PromptBuilder` object with the provided paths and settings.

            _read_file(self, file_path)
                Helper method to read the content of a file.

            build_prompt(self)
                Replaces placeholders with the actual content of files read during initialization and returns the formatted prompt string.
        """
        self.prompt_template = self._read_file(prompt_template_path)
        self.source_file = self._read_file(source_file_path)
        self.test_file = self._read_file(test_file_path)
        self.code_coverage_report = code_coverage_report

        # Conditionally fill in optional sections
        self.included_files = ADDITIONAL_INCLUDES_TEXT.format(included_files=included_files) if included_files else included_files
        self.additional_instructions = ADDITIONAL_INSTRUCTIONS_TEXT.format(additional_instructions=additional_instructions) if additional_instructions else additional_instructions
        self.failed_test_runs = FAILED_TESTS_TEXT.format(failed_test_runs=failed_test_runs) if failed_test_runs else failed_test_runs

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

    def build_prompt(self):
        """
        Replaces placeholders with the actual content of files read during initialization, and returns the formatted prompt.

        Parameters:
            None

        Returns:
            str: The formatted prompt string.
        """
        prompt = self.prompt_template.format(
            source_file=self.source_file,
            test_file=self.test_file,
            code_coverage_report=self.code_coverage_report,
            additional_includes_section=self.included_files,
            failed_tests_section=self.failed_test_runs,
            additional_instructions_text=self.additional_instructions,
        )

        return prompt
