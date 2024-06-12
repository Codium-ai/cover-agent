import argparse
import os
from cover_agent.CoverAgent import CoverAgent
from cover_agent.version import __version__
import logging


def parse_args():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description=f"Cover Agent v{__version__}")
    parser.add_argument(
        "--source-file-path", required=False, help="Path to the source file."
    )
    parser.add_argument(
        "--test-file-path", required=False, help="Path to the input test file."
    )
    parser.add_argument(
        "--source-file-directory", required=False, help="Path to the source directory"
    )
    parser.add_argument(
        "--test-file-directory", required=False, help="Path to the input test directory"
    )
    parser.add_argument(
        "--test-file-output-path",
        required=False,
        help="Path to the output test file.",
        default="",
        type=str,
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
        "--strict-coverage",
        action="store_true",
        help="If set, Cover-Agent will return a non-zero exit code if the desired code coverage is not achieved. Default: False.",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # If we pass only one source file path, just run the agent on the file.
    if args.source_file_path:
        print(f"Attempting to generate unit tests for {args.source_file_path} in {args.test_file_path} ...")
        agent = CoverAgent(args)
        agent.run()

    elif args.source_file_directory:
        print(f"Attempting to generate unit tests for all Python files in {args.source_file_directory} ...")
        source_files = os.listdir(args.source_file_directory)
        for file in source_files:
            if os.path.splitext(file)[1] == ".py":
                args.source_file_path = file

                test_file_directory = os.getcwd() + "/test"
                args.test_file_path = os.path.splitext(file)[0] + "_test.py"
                print(f"Attempting to generate unit tests for {args.source_file_path} in {args.test_file_path} ...")

                from pathlib import Path
                Path(test_file_directory).mkdir(parents=True, exist_ok=True)
                if not os.path.exists(args.test_file_path):
                    with open(args.test_file_path, 'w') as target_file:
                        target_file.write("")

                agent = CoverAgent(args)
                agent.run()

    else:
        print("Please provide either a source file path or directory.")
        return


if __name__ == "__main__":
    main()
