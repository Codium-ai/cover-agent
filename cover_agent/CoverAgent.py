import datetime
import os
import shutil
import sys
import wandb

from cover_agent.CustomLogger import CustomLogger
from cover_agent.ReportGenerator import ReportGenerator
from cover_agent.UnitTestGenerator import UnitTestGenerator


class CoverAgent:
    def __init__(self, args):
        """
        Initialize the CoverAgent with the provided arguments.

        Parameters:
            args: The arguments required for initialization.
        """
        self.args = args  # Store the arguments
        self.logger = CustomLogger.get_logger(__name__)  # Initialize the logger

        self._validate_paths()  # Validate the provided file paths
        self._duplicate_test_file()  # Duplicate the test file to the output path

        # Initialize the UnitTestGenerator with the provided arguments
        self.test_gen = UnitTestGenerator(
            source_file_path=args.source_file_path,
            test_file_path=args.test_file_output_path,
            code_coverage_report_path=args.code_coverage_report_path,
            test_command=args.test_command,
            test_command_dir=args.test_command_dir,
            included_files=args.included_files,
            coverage_type=args.coverage_type,
            desired_coverage=args.desired_coverage,
            additional_instructions=args.additional_instructions,
            llm_model=args.model,
            api_base=args.api_base,
        )

    def _validate_paths(self):
        """
        Validate the existence of the source and test file paths.

        Raises:
            FileNotFoundError: If the source or test file path does not exist.
        """
        # Check if the source file path exists
        if not os.path.isfile(self.args.source_file_path):
            raise FileNotFoundError(
                f"Source file not found at {self.args.source_file_path}"
            )
        # Check if the test file path exists
        if not os.path.isfile(self.args.test_file_path):
            raise FileNotFoundError(
                f"Test file not found at {self.args.test_file_path}"
            )

    def _duplicate_test_file(self):
        """
        Duplicate the test file to the output path if specified.
        """
        # Check if a specific output path is provided
        if self.args.test_file_output_path != "":
            # Copy the test file to the specified output path
            shutil.copy(self.args.test_file_path, self.args.test_file_output_path)
        else:
            # Use the same path if no specific output path is provided
            self.args.test_file_output_path = self.args.test_file_path

    def _initialize_wandb(self):
        """
        Initialize Weights & Biases logging if the API key is set.
        """
        # Check if the WANDB_API_KEY environment variable is set
        if "WANDB_API_KEY" in os.environ:
            # Login to WandB
            wandb.login(key=os.environ["WANDB_API_KEY"])
            # Generate a unique run name using the current time and date
            time_and_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            run_name = f"{self.args.model}_" + time_and_date
            # Initialize a new WandB run
            wandb.init(project="cover-agent", name=run_name)

    def _log_current_coverage(self):
        """
        Log the current and desired code coverage.
        """
        # Log the current code coverage
        self.logger.info(
            f"Current Coverage: {round(self.test_gen.current_coverage * 100, 2)}%"
        )
        # Log the desired code coverage
        self.logger.info(f"Desired Coverage: {self.test_gen.desired_coverage}%")

    def _run_tests(self):
        """
        Generate and validate tests to achieve the desired coverage.

        Returns:
            tuple: A tuple containing the list of test results and the iteration count.
        """
        iteration_count = 0  # Initialize iteration count
        test_results_list = []  # Initialize the list to store test results

        # Perform initial analysis of the test suite
        self.test_gen.initial_test_suite_analysis()

        # Loop until the desired coverage is achieved or the maximum iterations are reached
        while (
            self.test_gen.current_coverage < (self.test_gen.desired_coverage / 100)
            and iteration_count < self.args.max_iterations
        ):
            self._log_current_coverage()  # Log the current coverage

            # Generate new tests
            generated_tests_dict = self.test_gen.generate_tests(max_tokens=4096)

            # Validate each generated test and store the results
            for generated_test in generated_tests_dict.get("new_tests", []):
                test_result = self.test_gen.validate_test(
                    generated_test, generated_tests_dict
                )
                test_results_list.append(test_result)

            iteration_count += 1  # Increment the iteration count

            # Run coverage again if the desired coverage is not achieved
            if self.test_gen.current_coverage < (self.test_gen.desired_coverage / 100):
                self.test_gen.run_coverage()

        return (
            test_results_list,
            iteration_count,
        )  # Return the test results and iteration count

    def _handle_completion(self, iteration_count):
        """
        Handle the completion of the test generation process.

        Parameters:
            iteration_count (int): The number of iterations performed.
        """
        # Check if the desired coverage is achieved
        if self.test_gen.current_coverage >= (self.test_gen.desired_coverage / 100):
            self.logger.info(
                f"Reached above target coverage of {self.test_gen.desired_coverage}% (Current Coverage: {round(self.test_gen.current_coverage * 100, 2)}%) in {iteration_count} iterations."
            )
        elif iteration_count == self.args.max_iterations:
            # Handle the case where the maximum iteration limit is reached without achieving the desired coverage
            failure_message = f"Reached maximum iteration limit without achieving desired coverage. Current Coverage: {round(self.test_gen.current_coverage * 100, 2)}%"
            if self.args.strict_coverage:
                # Fail with exit code 2 if strict coverage is requested
                self.logger.error(failure_message)
                sys.exit(2)
            else:
                self.logger.info(failure_message)

    def _log_token_usage(self):
        """
        Log the total number of input and output tokens used.
        """
        # Log the total number of input tokens used by the LLM model
        self.logger.info(
            f"Total number of input tokens used for LLM model {self.test_gen.ai_caller.model}: {self.test_gen.total_input_token_count}"
        )
        # Log the total number of output tokens used by the LLM model
        self.logger.info(
            f"Total number of output tokens used for LLM model {self.test_gen.ai_caller.model}: {self.test_gen.total_output_token_count}"
        )

    def run(self):
        """
        Run the CoverAgent process to generate and validate tests, and report results.
        """
        self._initialize_wandb()  # Initialize WandB if the API key is set
        test_results_list, iteration_count = (
            self._run_tests()
        )  # Run the tests and get the results
        self._handle_completion(iteration_count)  # Handle the completion of the process
        self._log_token_usage()  # Log the token usage
        # Generate and save the report
        ReportGenerator.generate_report(test_results_list, self.args.report_filepath)
        # Finalize WandB logging if the API key is set
        if "WANDB_API_KEY" in os.environ:
            wandb.finish()
