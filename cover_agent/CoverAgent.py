import datetime
import os
import shutil
import sys
import wandb

from cover_agent.CustomLogger import CustomLogger
from cover_agent.ReportGenerator import ReportGenerator
from cover_agent.UnitTestGenerator import UnitTestGenerator
from cover_agent.UnitTestDB import UnitTestDB

class CoverAgent:
    def __init__(self, args):
        """
        Initialize the CoverAgent class with the provided arguments and run the test generation process.

        Parameters:
            args (Namespace): The parsed command-line arguments containing necessary information for test generation.

        Returns:
            None
        """
        self.args = args
        self.logger = CustomLogger.get_logger(__name__)

        self._validate_paths()
        self._duplicate_test_file()

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
            use_report_coverage_feature_flag=args.use_report_coverage_feature_flag,
        )

    def _validate_paths(self):
        """
        Validate the paths provided in the arguments.

        Raises:
            FileNotFoundError: If the source file or test file is not found at the specified paths.
        """
        # Ensure the source file exists
        if not os.path.isfile(self.args.source_file_path):
            raise FileNotFoundError(
                f"Source file not found at {self.args.source_file_path}"
            )
        # Ensure the test file exists
        if not os.path.isfile(self.args.test_file_path):
            raise FileNotFoundError(
                f"Test file not found at {self.args.test_file_path}"
            )
        # Create default DB file if not provided
        if not self.args.log_db_path:
            self.args.log_db_path = "cover_agent_unit_test_runs.db"
        # Connect to the test DB
        self.test_db = UnitTestDB(db_connection_string=f"sqlite:///{self.args.log_db_path}")

    def _duplicate_test_file(self):
        """
        Initialize the CoverAgent class with the provided arguments and run the test generation process.

        Parameters:
            args (Namespace): The parsed command-line arguments containing necessary information for test generation.

        Returns:
            None
        """
        # If the test file output path is set, copy the test file there
        if self.args.test_file_output_path != "":
            shutil.copy(self.args.test_file_path, self.args.test_file_output_path)
        else:
            # Otherwise, set the test file output path to the current test file
            self.args.test_file_output_path = self.args.test_file_path

    def run(self):
        """
        Run the test generation process.

        This method performs the following steps:

        1. Initialize the Weights & Biases run if the WANDS_API_KEY environment variable is set.
        2. Initialize variables to track progress.
        3. Run the initial test suite analysis.
        4. Loop until desired coverage is reached or maximum iterations are met.
        5. Generate new tests.
        6. Loop through each new test and validate it.
        7. Insert the test result into the database.
        8. Increment the iteration count.
        9. Check if the desired coverage has been reached.
        10. If the desired coverage has been reached, log the final coverage.
        11. If the maximum iteration limit is reached, log a failure message if strict coverage is specified.
        12. Provide metrics on total token usage.
        13. Generate a report.
        14. Finish the Weights & Biases run if it was initialized.
        """
        # Check if user has exported the WANDS_API_KEY environment variable
        if "WANDB_API_KEY" in os.environ:
            # Initialize the Weights & Biases run
            wandb.login(key=os.environ["WANDB_API_KEY"])
            time_and_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            run_name = f"{self.args.model}_" + time_and_date
            wandb.init(project="cover-agent", name=run_name)

        # Initialize variables to track progress
        iteration_count = 0
        test_results_list = []

        # Run initial test suite analysis
        self.test_gen.get_coverage_and_build_prompt()
        self.test_gen.initial_test_suite_analysis()

        # Loop until desired coverage is reached or maximum iterations are met
        while (
            self.test_gen.current_coverage < (self.test_gen.desired_coverage / 100)
            and iteration_count < self.args.max_iterations
        ):
            # Log the current coverage
            self.logger.info(
                f"Current Coverage: {round(self.test_gen.current_coverage * 100, 2)}%"
            )
            self.logger.info(f"Desired Coverage: {self.test_gen.desired_coverage}%")

            # Generate new tests
            generated_tests_dict = self.test_gen.generate_tests()

            # Loop through each new test and validate it
            for generated_test in generated_tests_dict.get("new_tests", []):
                # Validate the test and record the result
                test_result = self.test_gen.validate_test(
                    generated_test, self.args.run_tests_multiple_times
                )
                test_results_list.append(test_result)

                # Insert the test result into the database
                self.test_db.insert_attempt(test_result)

            # Increment the iteration count
            iteration_count += 1

            # Check if the desired coverage has been reached
            if self.test_gen.current_coverage < (self.test_gen.desired_coverage / 100):
                # Run the coverage tool again if the desired coverage hasn't been reached
                self.test_gen.run_coverage()

        # Log the final coverage
        if self.test_gen.current_coverage >= (self.test_gen.desired_coverage / 100):
            self.logger.info(
                f"Reached above target coverage of {self.test_gen.desired_coverage}% (Current Coverage: {round(self.test_gen.current_coverage * 100, 2)}%) in {iteration_count} iterations."
            )
        elif iteration_count == self.args.max_iterations:
            failure_message = f"Reached maximum iteration limit without achieving desired coverage. Current Coverage: {round(self.test_gen.current_coverage * 100, 2)}%"
            if self.args.strict_coverage:
                # User requested strict coverage (similar to "--cov-fail-under in pytest-cov"). Fail with exist code 2.
                self.logger.error(failure_message)
                sys.exit(2)
            else:
                self.logger.info(failure_message)

        # Provide metrics on total token usage
        self.logger.info(
            f"Total number of input tokens used for LLM model {self.test_gen.ai_caller.model}: {self.test_gen.total_input_token_count}"
        )
        self.logger.info(
            f"Total number of output tokens used for LLM model {self.test_gen.ai_caller.model}: {self.test_gen.total_output_token_count}"
        )

        # Generate a report
        # ReportGenerator.generate_report(test_results_list, self.args.report_filepath)
        self.test_db.dump_to_report(self.args.report_filepath)

        # Finish the Weights & Biases run if it was initialized
        if "WANDB_API_KEY" in os.environ:
            wandb.finish()
