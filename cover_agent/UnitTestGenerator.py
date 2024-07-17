import datetime
import logging
import os
import re
import json
from wandb.sdk.data_types.trace_tree import Trace

from cover_agent.Runner import Runner
from cover_agent.CoverageProcessor import CoverageProcessor
from cover_agent.CustomLogger import CustomLogger
from cover_agent.PromptBuilder import PromptBuilder
from cover_agent.AICaller import AICaller
from cover_agent.FilePreprocessor import FilePreprocessor
from cover_agent.utils import load_yaml
from cover_agent.settings.config_loader import get_settings


class UnitTestGenerator:
    def __init__(
        self,
        source_file_path: str,
        test_file_path: str,
        code_coverage_report_path: str,
        test_command: str,
        llm_model: str,
        api_base: str = "",
        test_command_dir: str = os.getcwd(),
        included_files: list = None,
        coverage_type="cobertura",
        desired_coverage: int = 90,  # Default to 90% coverage if not specified
        additional_instructions: str = "",
    ):
        """
        Initialize the UnitTestGenerator class with the provided parameters.

        Parameters:
            source_file_path (str): The path to the source file being tested.
            test_file_path (str): The path to the test file where generated tests will be written.
            code_coverage_report_path (str): The path to the code coverage report file.
            test_command (str): The command to run tests.
            llm_model (str): The language model to be used for test generation.
            api_base (str, optional): The base API url to use in case model is set to Ollama or Hugging Face. Defaults to an empty string.
            test_command_dir (str, optional): The directory where the test command should be executed. Defaults to the current working directory.
            included_files (list, optional): A list of paths to included files. Defaults to None.
            coverage_type (str, optional): The type of coverage report. Defaults to "cobertura".
            desired_coverage (int, optional): The desired coverage percentage. Defaults to 90.
            additional_instructions (str, optional): Additional instructions for test generation. Defaults to an empty string.

        Returns:
            None
        """
        # Class variables
        self.source_file_path = source_file_path
        self.test_file_path = test_file_path
        self.code_coverage_report_path = code_coverage_report_path
        self.test_command = test_command
        self.test_command_dir = test_command_dir
        self.included_files = self.get_included_files(included_files)
        self.coverage_type = coverage_type
        self.desired_coverage = desired_coverage
        self.additional_instructions = additional_instructions
        self.language = self.get_code_language(source_file_path)

        # Objects to instantiate
        self.ai_caller = AICaller(model=llm_model, api_base=api_base)

        # Get the logger instance from CustomLogger
        self.logger = CustomLogger.get_logger(__name__)

        # States to maintain within this class
        self.preprocessor = FilePreprocessor(self.test_file_path)
        self.failed_test_runs = []
        self.total_input_token_count = 0
        self.total_output_token_count = 0

        # Run coverage and build the prompt
        self.run_coverage()
        self.prompt = self.build_prompt()

    def get_code_language(self, source_file_path):
        """
        Get the programming language based on the file extension of the provided source file path.

        Parameters:
            source_file_path (str): The path to the source file for which the programming language needs to be determined.

        Returns:
            str: The programming language inferred from the file extension of the provided source file path. Defaults to 'unknown' if the language cannot be determined.
        """
        # Retrieve the mapping of languages to their file extensions from settings
        language_extension_map_org = get_settings().language_extension_map_org

        # Initialize a dictionary to map file extensions to their corresponding languages
        extension_to_language = {}

        # Populate the extension_to_language dictionary
        for language, extensions in language_extension_map_org.items():
            for ext in extensions:
                extension_to_language[ext] = language

        # Extract the file extension from the source file path
        extension_s = "." + source_file_path.rsplit(".")[-1]

        # Initialize the default language name as 'unknown'
        language_name = "unknown"

        # Check if the extracted file extension is in the dictionary
        if extension_s and (extension_s in extension_to_language):
            # Set the language name based on the file extension
            language_name = extension_to_language[extension_s]

        # Return the language name in lowercase
        return language_name.lower()

    def run_coverage(self):
        """
        Perform an initial build/test command to generate coverage report and get a baseline.

        Parameters:
        - None

        Returns:
        - None
        """
        # Perform an initial build/test command to generate coverage report and get a baseline
        self.logger.info(
            f'Running build/test command to generate coverage report: "{self.test_command}"'
        )
        stdout, stderr, exit_code, time_of_test_command = Runner.run_command(
            command=self.test_command, cwd=self.test_command_dir
        )
        assert (
            exit_code == 0
        ), f'Fatal: Error running test command. Are you sure the command is correct? "{self.test_command}"\nExit code {exit_code}. \nStdout: \n{stdout} \nStderr: \n{stderr}'

        # Instantiate CoverageProcessor and process the coverage report
        coverage_processor = CoverageProcessor(
            file_path=self.code_coverage_report_path,
            src_file_path=self.source_file_path,
            coverage_type=self.coverage_type,
        )

        # Use the process_coverage_report method of CoverageProcessor, passing in the time the test command was executed
        try:
            lines_covered, lines_missed, percentage_covered = (
                coverage_processor.process_coverage_report(
                    time_of_test_command=time_of_test_command
                )
            )

            # Process the extracted coverage metrics
            self.current_coverage = percentage_covered
            self.code_coverage_report = f"Lines covered: {lines_covered}\nLines missed: {lines_missed}\nPercentage covered: {round(percentage_covered * 100, 2)}%"
        except AssertionError as error:
            # Handle the case where the coverage report does not exist or was not updated after the test command
            self.logger.error(f"Error in coverage processing: {error}")
            # Optionally, re-raise the error or handle it as deemed appropriate for your application
            raise
        except (ValueError, NotImplementedError) as e:
            # Handle errors related to unsupported coverage report types or issues in parsing
            self.logger.warning(f"Error parsing coverage report: {e}")
            self.logger.info(
                "Will default to using the full coverage report. You will need to check coverage manually for each passing test."
            )
            with open(self.code_coverage_report_path, "r") as f:
                self.code_coverage_report = f.read()

    @staticmethod
    def get_included_files(included_files):
        """
        A method to read and concatenate the contents of included files into a single string.

        Parameters:
            included_files (list): A list of paths to included files.

        Returns:
            str: A string containing the concatenated contents of the included files, or an empty string if the input list is empty.
        """
        if included_files:
            included_files_content = []
            file_names = []
            for file_path in included_files:
                try:
                    with open(file_path, "r") as file:
                        included_files_content.append(file.read())
                        file_names.append(file_path)
                except IOError as e:
                    print(f"Error reading file {file_path}: {str(e)}")
            out_str = ""
            if included_files_content:
                for i, content in enumerate(included_files_content):
                    out_str += (
                        f"file_path: `{file_names[i]}`\ncontent:\n```\n{content}\n```\n"
                    )

            return out_str.strip()
        return ""

    def build_prompt(self):
        """
        Builds a prompt using the provided information to be used for generating tests.

        This method checks for the existence of failed test runs and then calls the PromptBuilder class to construct the prompt.
        The prompt includes details such as the source file path, test file path, code coverage report, included files,
        additional instructions, failed test runs, and the programming language being used.

        Returns:
            str: The generated prompt to be used for test generation.
        """
        # Check for existence of failed tests:
        if not self.failed_test_runs:
            failed_test_runs_value = ""
        else:
            failed_test_runs_value = ""
            try:
                for failed_test in self.failed_test_runs:
                    failed_test_dict = failed_test.get("code", {})
                    if not failed_test_dict:
                        continue
                    # dump dict to str
                    code = json.dumps(failed_test_dict)
                    if "error_message" in failed_test:
                        error_message = failed_test["error_message"]
                    else:
                        error_message = None
                    failed_test_runs_value += f"Failed Test:\n```\n{code}\n```\n"
                    if error_message:
                        failed_test_runs_value += (
                            f"Error message for test above:\n{error_message}\n\n\n"
                        )
                    else:
                        failed_test_runs_value += "\n\n"
            except Exception as e:
                self.logger.error(f"Error processing failed test runs: {e}")
                failed_test_runs_value = ""
        self.failed_test_runs = (
            []
        )  # Reset the failed test runs. we don't want a list which grows indefinitely, and will take all the prompt tokens

        # Call PromptBuilder to build the prompt
        self.prompt_builder = PromptBuilder(
            source_file_path=self.source_file_path,
            test_file_path=self.test_file_path,
            code_coverage_report=self.code_coverage_report,
            included_files=self.included_files,
            additional_instructions=self.additional_instructions,
            failed_test_runs=failed_test_runs_value,
            language=self.language,
        )

        return self.prompt_builder.build_prompt()

    def initial_test_suite_analysis(self):
        """
        Perform the initial analysis of the test suite structure.

        This method iterates through a series of attempts to analyze the test suite structure by interacting with the AI model.
        It constructs prompts based on specific files and calls to the AI model to gather information such as test headers indentation,
        relevant line numbers for inserting new tests, and relevant line numbers for inserting imports.
        The method handles multiple attempts to gather this information and raises exceptions if the analysis fails.

        Raises:
            Exception: If the test headers indentation cannot be analyzed successfully.
            Exception: If the relevant line number to insert new tests cannot be determined.

        Returns:
            None
        """
        try:
            test_headers_indentation = None
            allowed_attempts = 3
            counter_attempts = 0
            while (
                test_headers_indentation is None and counter_attempts < allowed_attempts
            ):
                prompt_headers_indentation = self.prompt_builder.build_prompt_custom(
                    file="analyze_suite_test_headers_indentation"
                )
                response, prompt_token_count, response_token_count = (
                    self.ai_caller.call_model(prompt=prompt_headers_indentation)
                )
                self.total_input_token_count += prompt_token_count
                self.total_output_token_count += response_token_count
                tests_dict = load_yaml(response)
                test_headers_indentation = tests_dict.get(
                    "test_headers_indentation", None
                )
                counter_attempts += 1

            if test_headers_indentation is None:
                raise Exception("Failed to analyze the test headers indentation")

            relevant_line_number_to_insert_tests_after = None
            relevant_line_number_to_insert_imports_after = None
            allowed_attempts = 3
            counter_attempts = 0
            while (
                not relevant_line_number_to_insert_tests_after
                and counter_attempts < allowed_attempts
            ):
                prompt_test_insert_line = self.prompt_builder.build_prompt_custom(
                    file="analyze_suite_test_insert_line"
                )
                response, prompt_token_count, response_token_count = (
                    self.ai_caller.call_model(prompt=prompt_test_insert_line)
                )
                self.total_input_token_count += prompt_token_count
                self.total_output_token_count += response_token_count
                tests_dict = load_yaml(response)
                relevant_line_number_to_insert_tests_after = tests_dict.get(
                    "relevant_line_number_to_insert_tests_after", None
                )
                relevant_line_number_to_insert_imports_after = tests_dict.get(
                    "relevant_line_number_to_insert_imports_after", None
                )
                counter_attempts += 1

            if not relevant_line_number_to_insert_tests_after:
                raise Exception(
                    "Failed to analyze the relevant line number to insert new tests"
                )

            self.test_headers_indentation = test_headers_indentation
            self.relevant_line_number_to_insert_tests_after = (
                relevant_line_number_to_insert_tests_after
            )
            self.relevant_line_number_to_insert_imports_after = (
                relevant_line_number_to_insert_imports_after
            )
        except Exception as e:
            self.logger.error(f"Error during initial test suite analysis: {e}")
            raise Exception("Error during initial test suite analysis")

    def generate_tests(self, max_tokens=4096, dry_run=False):
        """
        Generate tests using the AI model based on the constructed prompt.

        This method generates tests by calling the AI model with the constructed prompt.
        It handles both dry run and actual test generation scenarios. In a dry run, it returns canned test responses.
        In the actual run, it calls the AI model with the prompt and processes the response to extract test
        information such as test tags, test code, test name, and test behavior.

        Parameters:
            max_tokens (int, optional): The maximum number of tokens to use for generating tests. Defaults to 4096.
            dry_run (bool, optional): A flag indicating whether to perform a dry run without calling the AI model. Defaults to False.

        Returns:
            dict: A dictionary containing the generated tests with test tags, test code, test name, and test behavior. If an error occurs during test generation, an empty dictionary is returned.

        Raises:
            Exception: If there is an error during test generation, such as a parsing error while processing the AI model response.
        """
        self.prompt = self.build_prompt()

        if dry_run:
            response = "```def test_something():\n    pass```\n```def test_something_else():\n    pass```\n```def test_something_different():\n    pass```"
        else:
            response, prompt_token_count, response_token_count = (
                self.ai_caller.call_model(prompt=self.prompt, max_tokens=max_tokens)
            )
            self.total_input_token_count += prompt_token_count
            self.total_output_token_count += response_token_count
        try:
            tests_dict = load_yaml(
                response,
                keys_fix_yaml=["test_tags", "test_code", "test_name", "test_behavior"],
            )
            if tests_dict is None:
                return {}
        except Exception as e:
            self.logger.error(f"Error during test generation: {e}")
            # Record the error as a failed test attempt
            fail_details = {
                "status": "FAIL",
                "reason": f"Parsing error: {e}",
                "exit_code": None,  # No exit code as it's a parsing issue
                "stderr": str(e),
                "stdout": "",  # No output expected from a parsing error
                "test": response,  # Use the response that led to the error
            }
            # self.failed_test_runs.append(fail_details)
            tests_dict = []

        return tests_dict

    def validate_test(self, generated_test: dict, generated_tests_dict: dict):
        """
        Validate a generated test by inserting it into the test file, running the test, and checking for pass/fail.

        Parameters:
            generated_test (dict): The generated test to validate, containing test code and additional imports.
            generated_tests_dict (dict): A dictionary containing information about the generated tests.

        Returns:
            dict: A dictionary containing the status of the test validation, including pass/fail status, exit code, stderr, stdout, and the test details.
        """
        try:
            # Extract test code and imports from the generated test
            test_code, additional_imports = self.extract_test_code_and_imports(
                generated_test
            )
            # Adjust the indentation of the test code
            test_code_indented = self.adjust_indentation(test_code)

            if test_code_indented and self.relevant_line_number_to_insert_tests_after:
                # Append the generated test to the relevant line in the test file and save the original content
                original_content = self.append_generated_test(
                    test_code_indented, additional_imports
                )

                # Run the test using the Runner class
                stdout, stderr, exit_code, time_of_test_command = self.run_test()
                if exit_code != 0:
                    # Handle test failure and rollback changes
                    return self.handle_test_failure(
                        original_content, generated_test, stderr, stdout, exit_code
                    )

                try:
                    # Check if the code coverage has increased
                    new_percentage_covered = self.check_coverage_increase(
                        time_of_test_command
                    )
                    if new_percentage_covered <= self.current_coverage:
                        # Handle coverage failure and rollback changes
                        return self.handle_coverage_failure(
                            original_content, generated_test, stderr, stdout, exit_code
                        )
                except Exception as e:
                    # Handle runtime error during coverage verification
                    return self.handle_runtime_error(
                        original_content, generated_test, stderr, stdout, exit_code, e
                    )

                # Update current coverage and log success
                self.current_coverage = new_percentage_covered
                self.logger.info(
                    f"Test passed and coverage increased. Current coverage: {round(new_percentage_covered * 100, 2)}%"
                )
                return self.create_pass_response(
                    generated_test, stderr, stdout, exit_code
                )
        except Exception as e:
            # Log and return error response in case of any exception
            self.logger.error(f"Error validating test: {e}")
            return self.create_fail_response(
                generated_test, f"Error validating test: {e}"
            )

    def extract_test_code_and_imports(self, generated_test):
        """
        Extract test code and additional imports from the generated test.

        Parameters:
            generated_test (dict): The generated test containing test code and additional imports.

        Returns:
            tuple: A tuple containing the test code and additional imports as strings.
        """
        test_code = generated_test.get("test_code", "").rstrip()
        additional_imports = generated_test.get("new_imports_code", "").strip()
        # Remove surrounding quotes if present
        if (
            additional_imports
            and additional_imports[0] == '"'
            and additional_imports[-1] == '"'
        ):
            additional_imports = additional_imports.strip('"')
        if additional_imports == '""':
            additional_imports = ""
        return test_code, additional_imports

    def adjust_indentation(self, test_code):
        """
        Adjust the indentation of the test code to match the required indentation.

        Parameters:
            test_code (str): The test code to adjust indentation for.

        Returns:
            str: The indented test code.
        """
        needed_indent = self.test_headers_indentation
        test_code_indented = test_code
        if needed_indent:
            # Calculate the delta indent needed
            initial_indent = len(test_code) - len(test_code.lstrip())
            delta_indent = int(needed_indent) - initial_indent
            if delta_indent > 0:
                # Apply the indentation adjustment
                test_code_indented = "\n".join(
                    [delta_indent * " " + line for line in test_code.split("\n")]
                )
        return "\n" + test_code_indented.strip("\n") + "\n"

    def append_generated_test(self, test_code_indented, additional_imports):
        """
        Append the generated test to the relevant line in the test file.

        Parameters:
            test_code_indented (str): The indented test code.
            additional_imports (str): Additional imports required by the test code.

        Returns:
            str: The original content of the test file before modification.
        """
        # Read the original content of the test file
        with open(self.test_file_path, "r") as test_file:
            original_content = test_file.read()
        original_content_lines = original_content.split("\n")
        test_code_lines = test_code_indented.split("\n")
        # Insert the test code at the relevant line
        processed_test_lines = (
            original_content_lines[: self.relevant_line_number_to_insert_tests_after]
            + test_code_lines
            + original_content_lines[self.relevant_line_number_to_insert_tests_after :]
        )
        if (
            self.relevant_line_number_to_insert_imports_after
            and additional_imports
            and additional_imports not in processed_test_lines
        ):
            additional_imports_lines = additional_imports.split("\n")
            # Insert the additional imports at the relevant line
            processed_test_lines = (
                processed_test_lines[
                    : self.relevant_line_number_to_insert_imports_after
                ]
                + additional_imports_lines
                + processed_test_lines[
                    self.relevant_line_number_to_insert_imports_after :
                ]
            )
            self.relevant_line_number_to_insert_tests_after += len(
                additional_imports_lines
            )
        # Write the processed test lines back to the test file
        with open(self.test_file_path, "w") as test_file:
            test_file.write("\n".join(processed_test_lines))
        return original_content

    def run_test(self):
        """
        Run the test using the Runner class.

        Returns:
            tuple: A tuple containing stdout, stderr, exit code, and the time of the test command.
        """
        self.logger.info(
            f'Running test with the following command: "{self.test_command}"'
        )
        # Run the command using Runner and capture the output
        return Runner.run_command(command=self.test_command, cwd=self.test_command_dir)

    def handle_test_failure(
        self, original_content, generated_test, stderr, stdout, exit_code
    ):
        """
        Handle the case when a test fails.

        Parameters:
            original_content (str): The original content of the test file.
            generated_test (dict): The generated test that failed.
            stderr (str): The standard error output from the test run.
            stdout (str): The standard output from the test run.
            exit_code (int): The exit code from the test run.

        Returns:
            dict: A dictionary containing the details of the failed test.
        """
        # Rollback to the original content of the test file
        with open(self.test_file_path, "w") as test_file:
            test_file.write(original_content)
        self.logger.info(f"Skipping a generated test that failed")
        # Extract error message from stdout
        error_message = extract_error_message_python(stdout)
        # Create and log failure details
        fail_details = self.create_fail_response(
            generated_test, "Test failed", stderr, stdout, exit_code, error_message
        )
        self.failed_test_runs.append(fail_details)
        self.log_failure(
            test_name=generated_test.get("test_name"),
            prompt=self.prompt,
            error=fail_details["reason"],
            stack_trace=stderr,
            generated_code=generated_test.get("test_code"),
            input_data=generated_test.get("input_data"),
            env_details=self.get_environment_details(),
        )
        self.log_wandb_failure(fail_details)
        return fail_details

    def check_coverage_increase(self, time_of_test_command):
        """
        Check if the code coverage has increased.

        Parameters:
            time_of_test_command (datetime): The time the test command was run.

        Returns:
            float: The new percentage of code coverage.
        """
        # Process the coverage report to check for coverage increase
        new_coverage_processor = CoverageProcessor(
            file_path=self.code_coverage_report_path,
            src_file_path=self.source_file_path,
            coverage_type=self.coverage_type,
        )
        _, _, new_percentage_covered = new_coverage_processor.process_coverage_report(
            time_of_test_command=time_of_test_command
        )
        return new_percentage_covered

    def handle_coverage_failure(
        self, original_content, generated_test, stderr, stdout, exit_code
    ):
        """
        Handle the case when the coverage does not increase.

        Parameters:
            original_content (str): The original content of the test file.
            generated_test (dict): The generated test that did not increase coverage.
            stderr (str): The standard error output from the test run.
            stdout (str): The standard output from the test run.
            exit_code (int): The exit code from the test run.

        Returns:
            dict: A dictionary containing the details of the failed test due to coverage not increasing.
        """
        # Rollback to the original content of the test file
        with open(self.test_file_path, "w") as test_file:
            test_file.write(original_content)
        self.logger.info("Test did not increase coverage. Rolling back.")
        # Create and log failure details
        fail_details = self.create_fail_response(
            generated_test,
            "Coverage did not increase",
            stderr,
            stdout,
            exit_code,
            "did not increase code coverage",
        )
        self.failed_test_runs.append(fail_details)
        self.log_failure(
            test_name=generated_test.get("test_name"),
            prompt=self.prompt,
            error=fail_details["reason"],
            stack_trace=stderr,
            generated_code=generated_test.get("test_code"),
            input_data=generated_test.get("input_data"),
            env_details=self.get_environment_details(),
        )
        self.log_wandb_failure(fail_details)
        return fail_details

    def handle_runtime_error(
        self, original_content, generated_test, stderr, stdout, exit_code, exception
    ):
        """
        Handle runtime errors during coverage verification.

        Parameters:
            original_content (str): The original content of the test file.
            generated_test (dict): The generated test that caused the runtime error.
            stderr (str): The standard error output from the test run.
            stdout (str): The standard output from the test run.
            exit_code (int): The exit code from the test run.
            exception (Exception): The exception that was raised.

        Returns:
            dict: A dictionary containing the details of the runtime error.
        """
        self.logger.error(f"Error during coverage verification: {exception}")
        # Rollback to the original content of the test file
        with open(self.test_file_path, "w") as test_file:
            test_file.write(original_content)
        # Create and log failure details
        fail_details = self.create_fail_response(
            generated_test,
            "Runtime error",
            stderr,
            stdout,
            exit_code,
            "coverage verification error",
        )
        self.failed_test_runs.append(fail_details)
        self.log_failure(
            test_name=generated_test.get("test_name"),
            prompt=self.prompt,
            error=fail_details["reason"],
            stack_trace=stderr,
            generated_code=generated_test.get("test_code"),
            input_data=generated_test.get("input_data"),
            env_details=self.get_environment_details(),
        )
        return fail_details

    def create_pass_response(self, generated_test, stderr, stdout, exit_code):
        """
        Create a response dictionary for a passing test.

        Parameters:
            generated_test (dict): The generated test that passed.
            stderr (str): The standard error output from the test run.
            stdout (str): The standard output from the test run.
            exit_code (int): The exit code from the test run.

        Returns:
            dict: A dictionary containing the details of the passed test.
        """
        return {
            "status": "PASS",
            "reason": "",
            "exit_code": exit_code,
            "stderr": stderr,
            "stdout": stdout,
            "test": generated_test,
        }

    def create_fail_response(
        self,
        generated_test,
        reason,
        stderr=None,
        stdout=None,
        exit_code=None,
        error_message=None,
    ):
        """
        Create a response dictionary for a failed test.

        Parameters:
            generated_test (dict): The generated test that failed.
            reason (str): The reason for the failure.
            stderr (str, optional): The standard error output from the test run. Defaults to None.
            stdout (str, optional): The standard output from the test run. Defaults to None.
            exit_code (int, optional): The exit code from the test run. Defaults to None.
            error_message (str, optional): The error message from the failure. Defaults to None.

        Returns:
            dict: A dictionary containing the details of the failed test.
        """
        return {
            "status": "FAIL",
            "reason": reason,
            "exit_code": exit_code,
            "stderr": stderr,
            "stdout": stdout,
            "test": generated_test,
            "error_message": error_message,
        }

    def log_wandb_failure(self, fail_details):
        """
        Log failure details to WandB if the API key is present.

        Parameters:
            fail_details (dict): The details of the failed test.
        """
        if "WANDB_API_KEY" in os.environ:
            # Log the failure details to WandB
            root_span = Trace(
                name="fail_details_"
                + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                kind="llm",
                inputs={"test_code": fail_details["test"]},
                outputs=fail_details,
            )
            root_span.log(name="inference")


def extract_error_message_python(fail_message):
    """
    Extracts and returns the error message from the provided failure message.

    Parameters:
        fail_message (str): The failure message containing the error message to be extracted.

    Returns:
        str: The extracted error message from the failure message, or an empty string if no error message is found.

    """
    try:
        # Define a regular expression pattern to match the error message
        MAX_LINES = 20
        pattern = r"={3,} FAILURES ={3,}(.*?)(={3,}|$)"
        match = re.search(pattern, fail_message, re.DOTALL)
        if match:
            err_str = match.group(1).strip("\n")
            err_str_lines = err_str.split("\n")
            if len(err_str_lines) > MAX_LINES:
                # show last MAX_lines lines
                err_str = "...\n" + "\n".join(err_str_lines[-MAX_LINES:])
            return err_str
        return ""
    except Exception as e:
        logging.error(f"Error extracting error message: {e}")
        return ""
