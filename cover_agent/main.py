import argparse
import os
from cover_agent.CoverAgent import CoverAgent
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
        "--test-file-path", required=True, help="Path to the input test file."
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
    parser.add_argument(
        "--run-tests-multiple-times",
        type=int,
        default=1,
        help="Number of times to run the tests generated by Cover Agent. Default: %(default)s.",
    )
    parser.add_argument(
        "--use-report-coverage-feature-flag",
        action="store_true",
        help="Setting this to True considers the coverage of all the files in the coverage report. This means we consider a test as good if it increases coverage for a different file other than the source file. Default: False.",
    )
    parser.add_argument(
        "--log-db-path",
        default="",
        help="Path to optional log database. Default: %(default)s.",
    )
    parser.add_argument(
        "--diff-coverage",
        action="store_true",
        default=False,
        help="If set, Cover-Agent will only generate tests based on the diff between branches. Note: Requires git to be installed. Default: False.",
    )
    parser.add_argument( 
        "--branch",
        type=str,
        default="main",
        help="The branch to compare against when using --diff-coverage. Default: %(default)s.",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    agent = CoverAgent(args)
    agent.run()


if __name__ == "__main__":
    main()
