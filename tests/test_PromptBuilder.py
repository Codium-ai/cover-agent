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
            "cover_agent/prompt_template.md",
            "source_path",
            "test_path",
            "dummy content",
        )
        assert builder.prompt_template == "dummy content"
        assert builder.source_file == "dummy content"
        assert builder.test_file == "dummy content"
        assert builder.code_coverage_report == "dummy content"
        assert builder.included_files == ""  # Updated expected value

    def test_build_prompt_replaces_placeholders_correctly(self):
        builder = PromptBuilder(
            "cover_agent/prompt_template.md",
            "source_path",
            "test_path",
            "coverage_report",
            "Included Files Content",
            "Additional Instructions Content",
            "Failed Test Runs Content",
        )
        builder.prompt_template = "Template: {source_file}, Test: {test_file}, Coverage: {code_coverage_report}, Includes: {additional_includes_section}, Instructions: {additional_instructions_text}, Failed Tests: {failed_tests_section}"
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"
        builder.included_files = "Included Files Content"
        builder.additional_instructions = "Additional Instructions Content"
        builder.failed_test_runs = "Failed Test Runs Content"

        expected_prompt = "Template: Source Content, Test: Test Content, Coverage: Coverage Report Content, Includes: Included Files Content, Instructions: Additional Instructions Content, Failed Tests: Failed Test Runs Content"
        result = builder.build_prompt()
        assert result == expected_prompt

    def test_initialization_handles_file_read_errors(self, monkeypatch):
        def mock_open_raise(*args, **kwargs):
            raise IOError("File not found")

        monkeypatch.setattr("builtins.open", mock_open_raise)

        builder = PromptBuilder(
            "cover_agent/prompt_template.md",
            "source_path",
            "test_path",
            "coverage_report",
        )
        assert "Error reading cover_agent/prompt_template.md" in builder.prompt_template
        assert "Error reading source_path" in builder.source_file
        assert "Error reading test_path" in builder.test_file

    def test_empty_included_files_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            prompt_template_path="cover_agent/prompt_template.md",
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            included_files="Included Files Content",
        )
        # Directly read the real file content for the prompt template
        with open("cover_agent/prompt_template.md", "r") as f:
            builder.prompt_template = f.read()
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"
        builder.included_files = ""

        result = builder.build_prompt()
        assert "## Additional Includes" not in result

    def test_non_empty_included_files_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            prompt_template_path="cover_agent/prompt_template.md",
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            included_files="Included Files Content",
        )

        # Directly read the real file content for the prompt template
        with open("cover_agent/prompt_template.md", "r") as f:
            builder.prompt_template = f.read()

        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Additional Includes" in result
        assert "Included Files Content" in result

    def test_empty_additional_instructions_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            prompt_template_path="cover_agent/prompt_template.md",
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            additional_instructions="",
        )
        # Directly read the real file content for the prompt template
        with open("cover_agent/prompt_template.md", "r") as f:
            builder.prompt_template = f.read()
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Additional Instructions" not in result

    def test_empty_failed_test_runs_section_not_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            prompt_template_path="cover_agent/prompt_template.md",
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            failed_test_runs="",
        )
        # Directly read the real file content for the prompt template
        with open("cover_agent/prompt_template.md", "r") as f:
            builder.prompt_template = f.read()
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Previous Iterations Failed Tests" not in result

    def test_non_empty_additional_instructions_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            prompt_template_path="cover_agent/prompt_template.md",
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            additional_instructions="Additional Instructions Content",
        )
        # Directly read the real file content for the prompt template
        with open("cover_agent/prompt_template.md", "r") as f:
            builder.prompt_template = f.read()
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Additional Instructions" in result
        assert "Additional Instructions Content" in result

    def test_non_empty_failed_test_runs_section_in_prompt(self, monkeypatch):
        # Disable the monkeypatch for open within this test
        monkeypatch.undo()
        builder = PromptBuilder(
            prompt_template_path="cover_agent/prompt_template.md",
            source_file_path="source_path",
            test_file_path="test_path",
            code_coverage_report="coverage_report",
            failed_test_runs="Failed Test Runs Content",
        )
        # Directly read the real file content for the prompt template
        with open("cover_agent/prompt_template.md", "r") as f:
            builder.prompt_template = f.read()
        builder.source_file = "Source Content"
        builder.test_file = "Test Content"
        builder.code_coverage_report = "Coverage Report Content"

        result = builder.build_prompt()
        assert "## Previous Iterations Failed Tests" in result
        assert "Failed Test Runs Content" in result
