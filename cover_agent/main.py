import argparse
import os
from cover_agent.CustomLogger import CustomLogger
from cover_agent.ReportGenerator import ReportGenerator
from cover_agent.UnitTestGenerator import UnitTestGenerator
from cover_agent.version import __version__


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description=f"Cover Agent v{__version__}")
    parser.add_argument(
        "--source-file-path", required=True, help="Path to the source file."
    )
    parser.add_argument(
        "--test-file-path", required=True, help="Path to the output test file."
    )
    parser.add_argument(
        "--code-coverage-report-path",
        required=True,
        help="Path to the code coverage report file.",
    )
    parser.add_argument(
        "--test-command",
        required=True,
        help="The command to run tests and generate coverage report.",
    )
    parser.add_argument(
        "--test-command-dir",
        default=os.getcwd(),
        help="The directory to run the test command in. Default: %(default)s.",
    )
    parser.add_argument(
        "--included-files",
        default=None,
        nargs="*",
        help='List of files to include in the coverage. For example, "--included-files library1.c library2.c." Default: %(default)s.',
    )
    parser.add_argument(
        "--coverage-type",
        default="cobertura",
        help="Type of coverage report. Default: %(default)s.",
    )
    parser.add_argument(
        "--report-filepath",
        default="test_results.html",
        help="Path to the output report file. Default: %(default)s.",
    )
    parser.add_argument(
        "--desired-coverage",
        type=int,
        default=90,
        help="The desired coverage percentage. Default: %(default)s.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=10,
        help="The maximum number of iterations. Default: %(default)s.",
    )
    parser.add_argument(
        "--additional-instructions",
        default="",
        help="Any additional instructions you wish to append at the end of the prompt. Default: %(default)s.",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o",
        help="Which LLM model to use. Default: %(default)s.",
    )
    parser.add_argument(
        "--api-base",
        default="http://localhost:11434",
        help="The API url to use for Ollama or Hugging Face. Default: %(default)s.",
    )
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Generate the prompt only (i.e. do not run the test or call to the LLM). Default: False.",
    )

    return parser.parse_args()


def write_prompt_to_file(prompt_file_name, prompt):
    with open(prompt_file_name, "w") as test_file:
        test_file.write(prompt)


def main():
    # Constants
    GENERATED_PROMPT_NAME = "generated_prompt.md"

    # Parse arguments and configure logger
    args = parse_args()
    logger = CustomLogger.get_logger(__name__)

    # Calculate the absolute path where the script expects the markdown file
    markdown_path = os.path.join(os.path.dirname(__file__), "prompt_template.md")
    # Check if the file exists at the expected path
    if not os.path.exists(markdown_path):
        raise FileNotFoundError(f"Expected markdown file not found at {markdown_path}")

    # Validate all file paths
    # Check if the source file exists
    if not os.path.isfile(args.source_file_path):
        raise FileNotFoundError(f"Source file not found at {args.source_file_path}")
    # Check if the test file exists
    if not os.path.isfile(args.test_file_path):
        raise FileNotFoundError(f"Test file not found at {args.test_file_path}")

    # Instantiate and configure UnitTestGenerator
    test_gen = UnitTestGenerator(
        prompt_template_path=markdown_path,
        source_file_path=args.source_file_path,
        test_file_path=args.test_file_path,
        code_coverage_report_path=args.code_coverage_report_path,
        test_command=args.test_command,
        test_command_dir=args.test_command_dir,
        included_files=args.included_files,
        coverage_type=args.coverage_type,
        desired_coverage=args.desired_coverage,
        additional_instructions=args.additional_instructions,
        llm_model=args.model,
        api_base=args.api_base
    )

    # Write test_gen.prompt to a debug markdown file
    write_prompt_to_file(GENERATED_PROMPT_NAME, test_gen.prompt)

    # Run the test and generate the report if not in prompt only mode
    if not args.prompt_only:
        iteration_count = 0
        test_results_list = []

        # Run continuously until desired coverage has been met or we've reached the maximum iteration count
        while (
            test_gen.current_coverage < (test_gen.desired_coverage / 100)
            and iteration_count < args.max_iterations
        ):
            # Provide coverage feedback to user
            logger.info(
                f"Current Coverage: {round(test_gen.current_coverage * 100, 2)}%"
            )
            logger.info(f"Desired Coverage: {test_gen.desired_coverage}%")

            # Generate tests by making a call to the LLM
            generated_tests = test_gen.generate_tests(max_tokens=4096)

            # Write test_gen.prompt to a debug markdown file
            write_prompt_to_file(GENERATED_PROMPT_NAME, test_gen.prompt)

            # Validate each test and append the results to the test results list
            for generated_test in generated_tests:
                test_result = test_gen.validate_test(generated_test)
                test_results_list.append(test_result)

            # Increment the iteration counter
            iteration_count += 1

        if iteration_count == args.max_iterations:
            logger.info(
                "Reached maximum iteration limit without achieving desired coverage."
            )

        # Dump the test results to a report
        ReportGenerator.generate_report(test_results_list, "test_results.html")
    else:
        logger.info(
            f"Prompt only option requested. Skipping call to LLM. Prompt can be found at: {GENERATED_PROMPT_NAME}"
        )


if __name__ == "__main__":
    main()
