import logging
import os
import re
import time
import json
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
            for file_path in included_files:
                try:
                    with open(file_path, "r") as file:
                        included_files_content.append(file.read())
                except IOError as e:
                    print(f"Error reading file {file_path}: {str(e)}")
            return "\n".join(included_files_content) if included_files_content else None
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
                    failed_test_dict = failed_test.get('code', {})
                    if not failed_test_dict:
                        continue
                    # dump dict to str
                    code = json.dumps(failed_test_dict)
                    if 'error_message' in failed_test:
                        error_message = failed_test['error_message']
                    else:
                        error_message = None
                    failed_test_runs_value += f"Failed Test:\n```\n{code}\n```\n"
                    if error_message:
                        failed_test_runs_value += f"Error message for test above:\n{error_message}\n\n\n"
                    else:
                        failed_test_runs_value += "\n\n"
            except Exception as e:
                self.logger.error(f"Error processing failed test runs: {e}")
                failed_test_runs_value = ""
        self.failed_test_runs = []  # Reset the failed test runs. we don't want a list which grows indefinitely, and will take all the prompt tokens

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
        try:
            test_headers_indentation = None
            allowed_attempts = 3
            counter_attempts = 0
            while test_headers_indentation is None:
                prompt_test_headers_indentation = self.prompt_builder.build_prompt_custom(file=
                                                                                "analyze_suite_test_headers_indentation")
                response, prompt_token_count, response_token_count = (
                    self.ai_caller.call_model(prompt=prompt_test_headers_indentation)
                )
                tests_dict = load_yaml(response)
                test_headers_indentation = tests_dict.get('test_headers_indentation', None)
                counter_attempts += 1
                if counter_attempts >= allowed_attempts:
                    break
            if test_headers_indentation is None:
                raise Exception("Failed to analyze the test headers indentation")

            relevant_line_number_to_insert_after = None
            allowed_attempts = 3
            counter_attempts = 0
            while not relevant_line_number_to_insert_after:
                prompt_test_headers_indentation = self.prompt_builder.build_prompt_custom(file=
                                                                                "analyze_suite_test_insert_line")
                response, prompt_token_count, response_token_count = (
                    self.ai_caller.call_model(prompt=prompt_test_headers_indentation)
                )
                tests_dict = load_yaml(response)
                relevant_line_number_to_insert_after = tests_dict.get('relevant_line_number_to_insert_after', None)
                counter_attempts += 1
                if counter_attempts >= allowed_attempts:
                    break
            if not relevant_line_number_to_insert_after:
                raise Exception("Failed to analyze the relevant line number to insert new tests")

            self.test_headers_indentation = test_headers_indentation
            self.relevant_line_number_to_insert_after = relevant_line_number_to_insert_after
        except Exception as e:
            self.logger.error(f"Error during initial test suite analysis: {e}")
            raise "Error during initial test suite analysis"

    def generate_tests(self, max_tokens=4096, dry_run=False):
        self.prompt = self.build_prompt()

        if dry_run:
            response = "```def test_something():\n    pass```\n```def test_something_else():\n    pass```\n```def test_something_different():\n    pass```"
        else:
            response, prompt_token_count, response_token_count = (
                self.ai_caller.call_model(prompt=self.prompt, max_tokens=max_tokens)
            )
        self.logger.info(
            f"Total token used count for LLM model {self.ai_caller.model}: {prompt_token_count + response_token_count}"
        )
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
        try:
            # Step 0: no pre-process.
            # We asked the model that each generated test should be a self-contained independent test
            test_code = generated_test.get("test_code", "").rstrip()
            additional_imports = generated_test.get('new_imports_code', '').strip().strip('"')
            # check if additional_imports only contains '"':
            if additional_imports and additional_imports == '""':
                additional_imports = ''
            relevant_line_number_to_insert_after = self.relevant_line_number_to_insert_after
            needed_indent = self.test_headers_indentation
            # remove initial indent of the test code, and insert the needed indent
            test_code_indented = test_code
            if needed_indent:
                initial_indent = len(test_code) - len(test_code.lstrip())
                delta_indent = int(needed_indent) - initial_indent
                if delta_indent > 0:
                    test_code_indented = '\n'.join([delta_indent*' ' + line for line in test_code.split('\n')])
            test_code_indented = '\n'+test_code_indented.strip('\n') + '\n'

            if test_code_indented and relevant_line_number_to_insert_after:

                # Step 1: Append the generated test to the relevant line in the test file
                with open(self.test_file_path, "r") as test_file:
                    original_content = test_file.read()  # Store original content
                original_content_lines = original_content.split("\n")
                test_code_lines = test_code_indented.split("\n")
                # insert the test code at the relevant line
                processed_test_lines = original_content_lines[:relevant_line_number_to_insert_after] + test_code_lines + original_content_lines[relevant_line_number_to_insert_after:]
                processed_test = "\n".join(processed_test_lines)
                # insert the additional imports at the top of the file
                if additional_imports and additional_imports not in processed_test:
                    processed_test = additional_imports + "\n\n" + processed_test
                with open(self.test_file_path, "w") as test_file:
                    test_file.write(processed_test)

                # Step 2: Run the test using the Runner class
                self.logger.info(
                    f'Running test with the following command: "{self.test_command}"'
                )
                stdout, stderr, exit_code, time_of_test_command = Runner.run_command(
                    command=self.test_command, cwd=self.test_command_dir
                )

                # Step 3: Check for pass/fail from the Runner object
                if exit_code != 0:
                    # Test failed, roll back the test file to its original content
                    with open(self.test_file_path, "w") as test_file:
                        test_file.write(original_content)
                    self.logger.info(f"Skipping a generated test that failed")
                    fail_details = {
                        "status": "FAIL",
                        "reason": "Test failed",
                        "exit_code": exit_code,
                        "stderr": stderr,
                        "stdout": stdout,
                        "test": generated_test,
                    }

                    error_message = extract_error_message_python(fail_details["stdout"])
                    if error_message:
                        logging.error(f"Error message:\n{error_message}")

                    self.failed_test_runs.append(
                        {'code': generated_test, 'error_message': error_message}
                    )  # Append failure details to the list
                    return fail_details

                # If test passed, check for coverage increase
                try:
                    # Step 4: Check that the coverage has increased using the CoverageProcessor class
                    new_coverage_processor = CoverageProcessor(
                        file_path=self.code_coverage_report_path,
                        src_file_path=self.source_file_path,
                        coverage_type=self.coverage_type,
                    )
                    _, _, new_percentage_covered = (
                        new_coverage_processor.process_coverage_report(
                            time_of_test_command=time_of_test_command
                        )
                    )

                    if new_percentage_covered <= self.current_coverage:
                        # Coverage has not increased, rollback the test by removing it from the test file
                        with open(self.test_file_path, "w") as test_file:
                            test_file.write(original_content)
                        self.logger.info("Test did not increase coverage. Rolling back.")
                        fail_details = {
                            "status": "FAIL",
                            "reason": "Coverage did not increase",
                            "exit_code": exit_code,
                            "stderr": stderr,
                            "stdout": stdout,
                            "test": generated_test,
                        }
                        self.failed_test_runs.append(
                            {'code': fail_details["test"], 'error_message': 'did not increase code coverage'}
                        )  # Append failure details to the list
                        return fail_details
                except Exception as e:
                    # Handle errors gracefully
                    self.logger.error(f"Error during coverage verification: {e}")
                    # Optionally, roll back even in case of error
                    with open(self.test_file_path, "w") as test_file:
                        test_file.write(original_content)
                    fail_details = {
                        "status": "FAIL",
                        "reason": "Runtime error",
                        "exit_code": exit_code,
                        "stderr": stderr,
                        "stdout": stdout,
                        "test": generated_test,
                    }
                    self.failed_test_runs.append(
                        {'code': fail_details["test"], 'error_message': 'coverage verification error'}
                    )  # Append failure details to the list
                    return fail_details

                # If everything passed and coverage increased, update current coverage and log success
                self.current_coverage = new_percentage_covered
                self.logger.info(
                    f"Test passed and coverage increased. Current coverage: {round(new_percentage_covered * 100, 2)}%"
                )
                return {
                    "status": "PASS",
                    "reason": "",
                    "exit_code": exit_code,
                    "stderr": stderr,
                    "stdout": stdout,
                    "test": generated_test,
                }
        except Exception as e:
            self.logger.error(f"Error validating test: {e}")
            return {
                "status": "FAIL",
                "reason": f"Error validating test: {e}",
                "exit_code": None,
                "stderr": str(e),
                "stdout": "",
                "test": generated_test,
            }


def extract_error_message_python(fail_message):
    try:
        # Define a regular expression pattern to match the error message
        MAX_LINES = 15
        pattern = r'={3,} FAILURES ={3,}(.*?)(={3,}|$)'
        match = re.search(pattern, fail_message, re.DOTALL)
        if match:
            err_str = match.group(1).strip('\n')
            err_str_lines = err_str.split('\n')
            if len(err_str_lines) > MAX_LINES:
                # show last MAX_lines lines
                err_str = '...\n' + '\n'.join(err_str_lines[-MAX_LINES:])
            return err_str
        return ""
    except Exception as e:
        logging.error(f"Error extracting error message: {e}")
        return ""