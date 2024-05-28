import pytest
from unittest.mock import patch, mock_open
from cover_agent.PromptBuilder import PromptBuilder


class TestPromptBuilder:
    @pytest.fixture(autouse=True)
    def setup_method(self, monkeypatch):
        mock_open_obj = mock_open(read_data="dummy content")
        monkeypatch.setattr("builtins.open", mock_open_obj)
        self.mock_open_obj = mock_open_obj

    def test_initialization_reads_file_contents(self):
        builder = PromptBuilder(
            "source_path",
            "test_path",
            "dummy content",
        )
        assert builder.source_file == "dummy content"
        assert builder.test_file == "dummy content"
        assert builder.code_coverage_report == "dummy content"
        assert builder.included_files == ""  # Updated expected value

    def test_initialization_handles_file_read_errors(self, monkeypatch):
        def mock_open_raise(*args, **kwargs):
            raise IOError("File not found")

        monkeypatch.setattr("builtins.open", mock_open_raise)

        builder = PromptBuilder(
            "source_path",
            "test_path",
            "coverage_report",
        )
        assert "Error reading source_path" in builder.source_file
        assert "Error reading test_path" in builder.test_file

    def test_empty_included_files_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            included_files="Included Files Content",
        )
        # Directly read the real file content for the prompt template
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"
        builder.included_files = ""

        result = builder.build_prompt()
        assert "## Additional Includes" not in result["user"]

    def test_non_empty_included_files_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            included_files="Included Files Content",
        )

        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Additional Includes" in result["user"]
        assert "Included Files Content" in result["user"]

    def test_empty_additional_instructions_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            additional_instructions="",
        )
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Additional Instructions" not in result["user"]

    def test_empty_failed_test_runs_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            failed_test_runs="",
        )
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Previous Iterations Failed Tests" not in result["user"]

    def test_non_empty_additional_instructions_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            additional_instructions="Additional Instructions Content",
        )
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Additional Instructions" in result["user"]
        assert "Additional Instructions Content" in result["user"]

    # we currently disabled the logic to add failed test runs to the prompt
    def test_non_empty_failed_test_runs_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            failed_test_runs="Failed Test Runs Content",
        )
        # Directly read the real file content for the prompt template
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Previous Iterations Failed Tests" in result["user"]
        assert "Failed Test Runs Content" in result["user"]
