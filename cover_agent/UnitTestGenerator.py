from wandb.sdk.data_types.trace_tree import Trace
import datetime
import json
import logging
import os
import re

from cover_agent.AICaller import AICaller
from cover_agent.CoverageProcessor import CoverageProcessor
from cover_agent.CustomLogger import CustomLogger
from cover_agent.FilePreprocessor import FilePreprocessor
from cover_agent.PromptBuilder import PromptBuilder
from cover_agent.Runner import Runner
from cover_agent.settings.config_loader import get_settings
from cover_agent.utils import load_yaml


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
        use_report_coverage_feature_flag: bool = False,
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
            use_report_coverage_feature_flag (bool, optional): Setting this to True considers the coverage of all the files in the coverage report. 
                                                               This means we consider a test as good if it increases coverage for a different 
                                                               file other than the source file. Defaults to False.

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
        self.use_report_coverage_feature_flag = use_report_coverage_feature_flag
        self.last_coverage_percentages = {}
        self.llm_model = llm_model
        self.current_coverage = 0

        # Objects to instantiate
        self.ai_caller = AICaller(model=llm_model, api_base=api_base)

        # Get the logger instance from CustomLogger
        self.logger = CustomLogger.get_logger(__name__)

        # States to maintain within this class
        self.preprocessor = FilePreprocessor(self.test_file_path)
        self.failed_test_runs = []
        self.total_input_token_count = 0
        self.total_output_token_count = 0
        self.testing_framework = "Unknown"
        self.code_coverage_report = ""

        # Read self.source_file_path into a string
        with open(self.source_file_path, "r") as f:
            self.source_code = f.read()

    def get_coverage_and_build_prompt(self):
        """
        Run code coverage and build the prompt to be used for generating tests.

        Returns:
            None
        """
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
            use_report_coverage_feature_flag=self.use_report_coverage_feature_flag
        )

        # Use the process_coverage_report method of CoverageProcessor, passing in the time the test command was executed
        try:
            if self.use_report_coverage_feature_flag:
                self.logger.info(
                    "Using the report coverage feature flag to process the coverage report"
                )
                file_coverage_dict = coverage_processor.process_coverage_report(
                    time_of_test_command=time_of_test_command
                )
                total_lines_covered = 0
                total_lines_missed = 0
                total_lines = 0
                for key in file_coverage_dict:
                    lines_covered, lines_missed, percentage_covered, branch_covered = (
                        file_coverage_dict[key]
                    )
                    total_lines_covered += len(lines_covered)
                    total_lines_missed += len(lines_missed)
                    total_lines += len(lines_covered) + len(lines_missed)
                    if key == self.source_file_path:
                        self.last_source_file_coverage = percentage_covered
                    if key not in self.last_coverage_percentages:
                        self.last_coverage_percentages[key] =  0
                    self.last_coverage_percentages[key] = percentage_covered
                try:
                    percentage_covered = total_lines_covered / total_lines
                except ZeroDivisionError:
                    self.logger.error(f"ZeroDivisionError: Attempting to perform total_lines_covered / total_lines: {total_lines_covered} / {total_lines}.")
                    percentage_covered = 0

                self.logger.info(
                    f"Total lines covered: {total_lines_covered}, Total lines missed: {total_lines_missed}, Total lines: {total_lines}"
                )
                self.logger.info(    
                    f"coverage: Percentage {round(percentage_covered * 100, 2)}%"
                )
            else:
                lines_covered, lines_missed, percentage_covered, branches_covered = (
                    coverage_processor.process_coverage_report(
                        time_of_test_command=time_of_test_command
                    )
                )

            # Process the extracted coverage metrics
            self.current_coverage = percentage_covered
            self.branches_coverage = branches_covered
            self.code_coverage_report = f"Lines covered: {lines_covered}\nLines missed: {lines_missed}\nPercentage covered: {round(percentage_covered * 100, 2)}%\nBranches covered: {branches_covered}"
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
                    error_message = failed_test.get("error_message", None)
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
            testing_framework=self.testing_framework,
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
                self.ai_caller.model = "gpt-4o" if self.llm_model in ["o1-preview", "o1-mini"] else self.llm_model # Exception for OpenAI's new reasoning engines
                response, prompt_token_count, response_token_count = (
                    self.ai_caller.call_model(prompt=prompt_headers_indentation)
                )
                self.ai_caller.model = self.llm_model
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
                self.ai_caller.model = "gpt-4o" if self.llm_model in ["o1-preview", "o1-mini"] else self.llm_model # Exception for OpenAI's new reasoning engines
                response, prompt_token_count, response_token_count = (
                    self.ai_caller.call_model(prompt=prompt_test_insert_line)
                )
                self.ai_caller.model = self.llm_model
                self.total_input_token_count += prompt_token_count
                self.total_output_token_count += response_token_count
                tests_dict = load_yaml(response)
                relevant_line_number_to_insert_tests_after = tests_dict.get(
                    "relevant_line_number_to_insert_tests_after", None
                )
                relevant_line_number_to_insert_imports_after = tests_dict.get(
                    "relevant_line_number_to_insert_imports_after", None
                )
                self.testing_framework = tests_dict.get("testing_framework", "Unknown")
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

    def generate_tests(self, max_tokens=4096):
        """
        Generate tests using the AI model based on the constructed prompt.

        This method generates tests by calling the AI model with the constructed prompt.
        It handles both dry run and actual test generation scenarios. In a dry run, it returns canned test responses.
        In the actual run, it calls the AI model with the prompt and processes the response to extract test
        information such as test tags, test code, test name, and test behavior.

        Parameters:
            max_tokens (int, optional): The maximum number of tokens to use for generating tests. Defaults to 4096.

        Returns:
            dict: A dictionary containing the generated tests with test tags, test code, test name, and test behavior. If an error occurs during test generation, an empty dictionary is returned.

        Raises:
            Exception: If there is an error during test generation, such as a parsing error while processing the AI model response.
        """
        self.prompt = self.build_prompt()

        stream = False if self.llm_model in ["o1-preview", "o1-mini"] else True
        response, prompt_token_count, response_token_count = (
            self.ai_caller.call_model(prompt=self.prompt, max_tokens=max_tokens, stream=stream)
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

    def validate_test(self, generated_test: dict, num_attempts=1):
        """
        Validate a generated test by inserting it into the test file, running the test, and checking for pass/fail.

        Parameters:
            generated_test (dict): The generated test to validate, containing test code and additional imports.
            num_attempts (int, optional): The number of attempts to run the test. Defaults to 1.

        Returns:
            dict: A dictionary containing the status of the test validation, including pass/fail status, exit code, stderr, stdout, and the test details.

        Steps:
            0. Assume each generated test is a self-contained independent test.
            1. Extract the test code and additional imports from the generated test.
            2. Clean up the additional imports if necessary.
            3. Determine the relevant line numbers for inserting tests and imports.
            4. Adjust the indentation of the test code to match the required indentation.
            5. Insert the test code and additional imports into the test file at the relevant lines.
            6. Run the test using the Runner class.
            7. Check the exit code to determine if the test passed or failed.
            8. If the test failed, roll back the test file to its original content and log the failure.
            9. If the test passed, check if the code coverage has increased using the CoverageProcessor class.
            10. If the coverage has not increased, roll back the test file and log the failure.
            11. If the coverage has increased, update the current coverage and log the success.
            12. Handle any exceptions that occur during the validation process, log the errors, and roll back the test file if necessary.
            13. Log additional details and error messages for failed tests, and optionally, use the Trace class for detailed logging if 'WANDB_API_KEY' is present in the environment variables.
        """
        # Store original content of the test file
        with open(self.test_file_path, "r") as test_file:
            original_content = test_file.read()

        try:
            # Step 0: no pre-process.
            # We asked the model that each generated test should be a self-contained independent test
            test_code = generated_test.get("test_code", "").rstrip()
            additional_imports = generated_test.get("new_imports_code", "").strip()
            if (
                additional_imports
                and additional_imports[0] == '"'
                and additional_imports[-1] == '"'
            ):
                additional_imports = additional_imports.strip('"')

            # check if additional_imports only contains '"':
            if additional_imports and additional_imports == '""':
                additional_imports = ""
            relevant_line_number_to_insert_tests_after = (
                self.relevant_line_number_to_insert_tests_after
            )
            relevant_line_number_to_insert_imports_after = (
                self.relevant_line_number_to_insert_imports_after
            )

            needed_indent = self.test_headers_indentation
            # remove initial indent of the test code, and insert the needed indent
            test_code_indented = test_code
            if needed_indent:
                initial_indent = len(test_code) - len(test_code.lstrip())
                delta_indent = int(needed_indent) - initial_indent
                if delta_indent > 0:
                    test_code_indented = "\n".join(
                        [delta_indent * " " + line for line in test_code.split("\n")]
                    )
            test_code_indented = "\n" + test_code_indented.strip("\n") + "\n"

            if test_code_indented and relevant_line_number_to_insert_tests_after:
                # Step 1: Insert the generated test to the relevant line in the test file
                additional_imports_lines = ""
                original_content_lines = original_content.split("\n")
                test_code_lines = test_code_indented.split("\n")
                # insert the test code at the relevant line
                processed_test_lines = (
                    original_content_lines[:relevant_line_number_to_insert_tests_after]
                    + test_code_lines
                    + original_content_lines[
                        relevant_line_number_to_insert_tests_after:
                    ]
                )
                # insert the additional imports at line 'relevant_line_number_to_insert_imports_after'
                processed_test = "\n".join(processed_test_lines)
                if (
                    relevant_line_number_to_insert_imports_after
                    and additional_imports
                    and additional_imports not in processed_test
                ):
                    additional_imports_lines = additional_imports.split("\n")
                    processed_test_lines = (
                        processed_test_lines[
                            :relevant_line_number_to_insert_imports_after
                        ]
                        + additional_imports_lines
                        + processed_test_lines[
                            relevant_line_number_to_insert_imports_after:
                        ]
                    )
                processed_test = "\n".join(processed_test_lines)
                with open(self.test_file_path, "w") as test_file:
                    test_file.write(processed_test)
                    test_file.flush()

                # Step 2: Run the test using the Runner class
                # Run the test command multiple times if num_attempts > 1
                for i in range(num_attempts):
                    self.logger.info(
                        f'Running test with the following command: "{self.test_command}"'
                    )
                    stdout, stderr, exit_code, time_of_test_command = Runner.run_command(
                        command=self.test_command, cwd=self.test_command_dir
                    )
                    if exit_code != 0:
                        break
                

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
                        "language": self.language,
                        "prompt": self.prompt["user"],
                        "source_file": self.source_code,
                        "original_test_file": original_content,
                        "processed_test_file": processed_test,
                    }

                    error_message = self.extract_error_message(stderr=fail_details["stderr"], stdout=fail_details["stdout"])
                    if error_message:
                        logging.error(f"Error message summary:\n{error_message}")

                    self.failed_test_runs.append(
                        {"code": generated_test, "error_message": error_message}
                    )  # Append failure details to the list

                    if "WANDB_API_KEY" in os.environ:
                        fail_details["error_message"] = error_message
                        root_span = Trace(
                            name="fail_details_"
                            + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                            kind="llm",  # kind can be "llm", "chain", "agent" or "tool
                            inputs={"test_code": fail_details["test"]},
                            outputs=fail_details,
                        )
                        root_span.log(name="inference")

                    return fail_details

                # If test passed, check for coverage increase
                try:
                    # Step 4: Check that the coverage has increased using the CoverageProcessor class
                    new_coverage_processor = CoverageProcessor(
                        file_path=self.code_coverage_report_path,
                        src_file_path=self.source_file_path,
                        coverage_type=self.coverage_type,
                        use_report_coverage_feature_flag=self.use_report_coverage_feature_flag,
                    )
                    coverage_percentages = {}

                    if self.use_report_coverage_feature_flag:
                        self.logger.info(
                            "Using the report coverage feature flag to process the coverage report"
                        )
                        file_coverage_dict = new_coverage_processor.process_coverage_report(
                            time_of_test_command=time_of_test_command
                        )
                        total_lines_covered = 0
                        total_lines_missed = 0
                        total_lines = 0
                        for key in file_coverage_dict:
                            lines_covered, lines_missed, percentage_covered = (
                                file_coverage_dict[key]
                            )
                            total_lines_covered += len(lines_covered)
                            total_lines_missed += len(lines_missed)
                            total_lines += len(lines_covered) + len(lines_missed)
                            if key not in coverage_percentages:
                                coverage_percentages[key] = 0
                            coverage_percentages[key] = percentage_covered

                        new_percentage_covered = total_lines_covered / total_lines
                    else:
                        _, _, new_percentage_covered, new_branches_covered = (
                            new_coverage_processor.process_coverage_report(
                                time_of_test_command=time_of_test_command
                            )
                        )

                    if new_percentage_covered <= self.current_coverage:
                        # Coverage has not increased, rollback the test by removing it from the test file
                        with open(self.test_file_path, "w") as test_file:
                            test_file.write(original_content)
                            test_file.flush()
                        self.logger.info(
                            "Test did not increase coverage. Rolling back."
                        )
                        fail_details = {
                            "status": "FAIL",
                            "reason": "Coverage did not increase",
                            "exit_code": exit_code,
                            "stderr": stderr,
                            "stdout": stdout,
                            "test": generated_test,
                            "language": self.language,
                            "prompt": self.prompt["user"],
                            "source_file": self.source_code,
                            "original_test_file": original_content,
                            "processed_test_file": processed_test,
                        }
                        self.failed_test_runs.append(
                            {
                                "code": fail_details["test"],
                                "error_message": "Code coverage did not increase",
                            }
                        )  # Append failure details to the list

                        if "WANDB_API_KEY" in os.environ:
                            root_span = Trace(
                                name="fail_details_"
                                + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
                                kind="llm",  # kind can be "llm", "chain", "agent" or "tool
                                inputs={"test_code": fail_details["test"]},
                                outputs=fail_details,
                            )
                            root_span.log(name="inference")

                        return fail_details
                except Exception as e:
                    # Handle errors gracefully
                    self.logger.error(f"Error during coverage verification: {e}")
                    # roll back even in case of error
                    with open(self.test_file_path, "w") as test_file:
                        test_file.write(original_content)
                        test_file.flush()

                    fail_details = {
                        "status": "FAIL",
                        "reason": "Runtime error",
                        "exit_code": exit_code,
                        "stderr": stderr,
                        "stdout": stdout,
                        "test": generated_test,
                        "language": self.language,
                        "prompt": self.prompt["user"],
                        "source_file": self.source_code,
                        "original_test_file": original_content,
                        "processed_test_file": processed_test,
                    }
                    self.failed_test_runs.append(
                        {
                            "code": fail_details["test"],
                            "error_message": "Coverage verification error",
                        }
                    )  # Append failure details to the list
                    return fail_details

                # If we got here, everything passed and coverage increased - update current coverage and log success,
                # and increase 'relevant_line_number_to_insert_tests_after' by the number of imports lines added
                self.relevant_line_number_to_insert_tests_after += len(
                    additional_imports_lines
                )  # this is important, otherwise the next test will be inserted at the wrong line

                self.current_coverage = new_percentage_covered
                self.branches_coverage = new_branches_covered

                for key in coverage_percentages:
                    if key not in self.last_coverage_percentages:
                        self.last_coverage_percentages[key] = 0
                    if coverage_percentages[key] > self.last_coverage_percentages[key] and key == self.source_file_path.split("/")[-1]:
                        self.logger.info(
                            f"Coverage for provided source file: {key} increased from {round(self.last_coverage_percentages[key] * 100, 2)} to {round(coverage_percentages[key] * 100, 2)}"
                        )
                    elif coverage_percentages[key] > self.last_coverage_percentages[key]:
                        self.logger.info(
                            f"Coverage for non-source file: {key} increased from {round(self.last_coverage_percentages[key] * 100, 2)} to {round(coverage_percentages[key] * 100, 2)}"
                        )
                    self.last_coverage_percentages[key] = coverage_percentages[key]

                self.logger.info(
                    f"Test passed and coverage increased. Current line coverage: {round(new_percentage_covered * 100, 2)}%, Current Branch coverage: {round(new_branches_covered * 100 , 2)}%"
                )
                return {
                    "status": "PASS",
                    "reason": "",
                    "exit_code": exit_code,
                    "stderr": stderr,
                    "stdout": stdout,
                    "test": generated_test,
                    "language": self.language,
                    "prompt": self.prompt["user"],
                    "source_file": self.source_code,
                    "original_test_file": original_content,
                    "processed_test_file": processed_test,
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
                "language": self.language,
                "prompt": self.prompt["user"],
                "source_file": self.source_code,
                "original_test_file": original_content,
                "processed_test_file": "N/A",
            }

    def to_dict(self):
        return {
            "source_file_path": self.source_file_path,
            "test_file_path": self.test_file_path,
            "code_coverage_report_path": self.code_coverage_report_path,
            "test_command": self.test_command,
            "llm_model": self.llm_model,
            "test_command_dir": self.test_command_dir,
            "included_files": self.included_files,
            "coverage_type": self.coverage_type,
            "desired_coverage": self.desired_coverage,
            "additional_instructions": self.additional_instructions,
        }

    def to_json(self):
        return json.dumps(self.to_dict())


    def extract_error_message(self, stderr, stdout):
        """
        Extracts the error message from the provided stderr and stdout outputs.

        Updates the PromptBuilder object with the stderr and stdout, builds a custom prompt for analyzing test run failures,
        calls the language model to analyze the prompt, and loads the response into a dictionary.
        
        Returns the error summary from the loaded YAML data or a default error message if unable to summarize.
        Logs errors encountered during the process.

        Parameters:
            stderr (str): The standard error output from the test run.
            stdout (str): The standard output from the test run.

        Returns:
            str: The error summary extracted from the response or a default error message if extraction fails.
        """
        try:
            # Update the PromptBuilder object with stderr and stdout
            self.prompt_builder.stderr_from_run = stderr
            self.prompt_builder.stdout_from_run = stdout

            # Build the prompt
            prompt_headers_indentation = self.prompt_builder.build_prompt_custom(
                file="analyze_test_run_failure"
            )

            # Run the analysis via LLM
            self.ai_caller.model = "gpt-4o" if self.llm_model in ["o1-preview", "o1-mini"] else self.llm_model # Exception for OpenAI's new reasoning engines
            response, prompt_token_count, response_token_count = (
                self.ai_caller.call_model(prompt=prompt_headers_indentation, stream=False)
            )
            self.ai_caller.model = self.llm_model # Reset
            self.total_input_token_count += prompt_token_count
            self.total_output_token_count += response_token_count
            tests_dict = load_yaml(response)
            
            return tests_dict.get("error_summary", f"ERROR: Unable to summarize error message from inputs. STDERR: {stderr}\nSTDOUT: {stdout}.")
        except Exception as e:
            logging.error(f"ERROR: Unable to extract error message from inputs using LLM.\nSTDERR: {stderr}\nSTDOUT: {stdout}")
            logging.error(f"Error extracting error message: {e}")
            return ""