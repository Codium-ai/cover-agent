import pytest
from cover_agent.ReportGenerator import (
    ReportGenerator,
)  # Adjust the import according to your project structure


class TestReportGeneration:
    @pytest.fixture
    def sample_results(self):
        # This should mimic the structure of the data you're passing to the report generator
        return [
            {
                "status": "pass",
                "reason": "",
                "exit_code": 0,
                "stderr": "",
                "stdout": "test session starts platform linux -- Python 3.10.12, pytest-7.0.1",
                "test": "def test_current_date():\n    response = client.get('/current-date')\n    assert response.status_code == 200\n    assert 'date' in response.json()",
            },
            # Add more sample results as needed
        ]

    @pytest.fixture
    def expected_output(self):
        # This is a simplified version of what you expect to be in the generated HTML file
        # For real testing, you'd want this to be more complete and accurate
        expected_start = "<html>"
        expected_table_header = "<th>Status</th>"
        expected_row_content = "test_current_date"
        expected_end = "</html>"
        return expected_start, expected_table_header, expected_row_content, expected_end

    def test_generate_report(self, sample_results, expected_output, tmp_path):
        report_path = tmp_path / "test_report.html"
        ReportGenerator.generate_report(sample_results, str(report_path))

        with open(report_path, "r") as file:
            content = file.read()

        # Verify that the expected pieces are present in the output
        assert expected_output[1] in content
        assert expected_output[2] in content
        assert expected_output[3] in content

        # You might want to add more detailed checks to ensure the content is exactly as expected
