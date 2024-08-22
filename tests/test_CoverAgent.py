import os
import argparse
from unittest.mock import patch, MagicMock
import pytest
from cover_agent.CoverAgent import CoverAgent
from cover_agent.main import parse_args


class TestCoverAgent:
    def test_parse_args(self):
        with patch(
            "sys.argv",
            [
                "program.py",
                "--source-file-path",
                "test_source.py",
                "--test-file-path",
                "test_file.py",
                "--code-coverage-report-path",
                "coverage_report.xml",
                "--test-command",
                "pytest",
                "--max-iterations",
                "10",
            ],
        ):
            args = parse_args()
            assert args.source_file_path == "test_source.py"
            assert args.test_file_path == "test_file.py"
            assert args.code_coverage_report_path == "coverage_report.xml"
            assert args.test_command == "pytest"
            assert args.test_command_dir == os.getcwd()
            assert args.included_files is None
            assert args.coverage_type == "cobertura"
            assert args.report_filepath == "test_results.html"
            assert args.desired_coverage == 90
            assert args.max_iterations == 10

    @patch("cover_agent.CoverAgent.UnitTestGenerator")
    @patch("cover_agent.CoverAgent.ReportGenerator")
    @patch("cover_agent.CoverAgent.os.path.isfile")
    def test_agent_source_file_not_found(
        self, mock_isfile, mock_report_generator, mock_unit_cover_agent
    ):
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
        )
        parse_args = lambda: args
        mock_isfile.return_value = False

        with patch("cover_agent.main.parse_args", parse_args):
            with pytest.raises(FileNotFoundError) as exc_info:
                agent = CoverAgent(args)

        assert (
            str(exc_info.value) == f"Source file not found at {args.source_file_path}"
        )

        mock_unit_cover_agent.assert_not_called()
        mock_report_generator.generate_report.assert_not_called()

    @patch("cover_agent.CoverAgent.os.path.exists")
    @patch("cover_agent.CoverAgent.os.path.isfile")
    @patch("cover_agent.CoverAgent.UnitTestGenerator")
    def test_agent_test_file_not_found(
        self, mock_unit_cover_agent, mock_isfile, mock_exists
    ):
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            code_coverage_report_path="coverage_report.xml",
            test_command="pytest",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            prompt_only=False,
        )
        parse_args = lambda: args
        mock_isfile.side_effect = [True, False]
        mock_exists.return_value = True

        with patch("cover_agent.main.parse_args", parse_args):
            with pytest.raises(FileNotFoundError) as exc_info:
                agent = CoverAgent(args)

        assert str(exc_info.value) == f"Test file not found at {args.test_file_path}"

    @patch("cover_agent.CoverAgent.shutil.copy")
    @patch("cover_agent.CoverAgent.os.path.isfile", return_value=True)
    def test_duplicate_test_file_with_output_path(self, mock_isfile, mock_copy):
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            test_file_output_path="output_test_file.py",
            code_coverage_report_path="coverage_report.xml",
            test_command="echo hello",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            additional_instructions="",
            model="openai/test-model",
            api_base="openai/test-api",
            use_report_coverage_feature_flag=False
        )

        with pytest.raises(AssertionError) as exc_info:
            agent = CoverAgent(args)
            agent._duplicate_test_file()

        assert "Fatal: Coverage report" in str(exc_info.value)
        mock_copy.assert_called_once_with(args.test_file_path, args.test_file_output_path)

    @patch("cover_agent.CoverAgent.os.path.isfile", return_value=True)
    def test_duplicate_test_file_without_output_path(self, mock_isfile):
        args = argparse.Namespace(
            source_file_path="test_source.py",
            test_file_path="test_file.py",
            test_file_output_path="",
            code_coverage_report_path="coverage_report.xml",
            test_command="echo hello",
            test_command_dir=os.getcwd(),
            included_files=None,
            coverage_type="cobertura",
            report_filepath="test_results.html",
            desired_coverage=90,
            max_iterations=10,
            additional_instructions="",
            model="openai/test-model",
            api_base="openai/test-api",
            use_report_coverage_feature_flag=False
        )

        with pytest.raises(AssertionError) as exc_info:
            agent = CoverAgent(args)
            agent._duplicate_test_file()

        assert "Fatal: Coverage report" in str(exc_info.value)
        assert args.test_file_output_path == args.test_file_path

