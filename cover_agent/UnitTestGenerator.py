import os
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
            f'Running initial build/test command to generate coverage report: "{self.test_command}"'
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
            filename=os.path.basename(self.source_file_path),
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
            failed_test_runs_value = json.dumps(self.failed_test_runs).replace(
                "\\n", "\n"
            )

        # Call PromptBuilder to build the prompt
        prompt = PromptBuilder(
            source_file_path=self.source_file_path,
            test_file_path=self.test_file_path,
            code_coverage_report=self.code_coverage_report,
            included_files=self.included_files,
            additional_instructions=self.additional_instructions,
            failed_test_runs=failed_test_runs_value,
            language=self.language,
        )

        return prompt.build_prompt()

    def generate_tests(self, max_tokens=4096, dry_run=False):
        """
        Generate test cases using the AI model based on the provided prompt.

        This method generates test cases by calling the AI model with the constructed prompt.
        If 'dry_run' is set to True, placeholder test cases are returned.
        Otherwise, the AI model is invoked with the prompt to generate actual test cases.
        The method logs the total token count used by the language model.

        Parameters:
            max_tokens (int, optional): The maximum number of tokens to use for generating tests. Defaults to 4096.
            dry_run (bool, optional): If True, placeholder test cases are returned without invoking the AI model. Defaults to False.

        Returns:
            list: A list of generated test cases as strings.
            If an error occurs during test generation, an empty list is returned, and the error is recorded in the 'failed_test_runs' attribute.
        """
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
                raise ValueError("Failed to parse tests from YAML")
            tests_list = [t["test_code"].rstrip() for t in tests_dict["tests"]]
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
            self.failed_test_runs.append(fail_details)
            tests_list = []  # Return an empty list or handle accordingly

        return tests_list

    def validate_test(self, generated_test: str):
        """
        Validate a single generated test case by running it and checking coverage.

        This function appends the generated test to the test file, runs it, and checks the output.
        If the test fails or does not increase coverage, it rolls back changes and records the failure.

        Parameters:
            generated_test (str): The test code to validate.

        Returns:
            dict: A dictionary containing the test result status, reason for failure (if any),
                stdout, stderr, exit code, and the test itself.
        """
        # Step 0: Run the test through the preprocessor rule set
        # processed_test = self.preprocessor.process_file(generated_test)

        # Step 0: no pre-process.
        # We asked the model that each generated test should be a self-contained independent test
        processed_test = generated_test.strip('\n')

        # Step 1: Append the generated test to the test file and save the original content
        with open(self.test_file_path, "r+") as test_file:
            original_content = test_file.read()  # Store original content
            test_file.write(
                "\n"
                + ("\n" if not original_content.endswith("\n") else "")
                + processed_test
                + "\n"
            )  # Append the new test at the end

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
            self.logger.warning(f"Skipping a generated test that failed")
            fail_details = {
                "status": "FAIL",
                "reason": "Test failed",
                "exit_code": exit_code,
                "stderr": stderr,
                "stdout": stdout,
                "test": generated_test,
            }
            self.failed_test_runs.append(
                fail_details["test"]
            )  # Append failure details to the list
            return fail_details

        # If test passed, check for coverage increase
        try:
            # Step 4: Check that the coverage has increased using the CoverageProcessor class
            new_coverage_processor = CoverageProcessor(
                file_path=self.code_coverage_report_path,
                filename=os.path.basename(self.source_file_path),
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
                    fail_details["test"]
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
                fail_details["test"]
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
