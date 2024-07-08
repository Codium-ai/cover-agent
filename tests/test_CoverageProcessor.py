import pytest
import xml.etree.ElementTree as ET
from cover_agent.CoverageProcessor import CoverageProcessor


@pytest.fixture
def mock_xml_tree(monkeypatch):
    """
    Creates a mock function to simulate the ET.parse method, returning a mocked XML tree structure.
    """

    def mock_parse(file_path):
        # Mock XML structure for the test
        xml_str = """<coverage>
                        <packages>
                            <package>
                                <classes>
                                    <class filename="app.py">
                                        <lines>
                                            <line number="1" hits="1"/>
                                            <line number="2" hits="0"/>
                                        </lines>
                                    </class>
                                </classes>
                            </package>
                        </packages>
                     </coverage>"""
        root = ET.ElementTree(ET.fromstring(xml_str))
        return root

    monkeypatch.setattr(ET, "parse", mock_parse)


class TestCoverageProcessor:
    @pytest.fixture
    def processor(self):
        # Initializes CoverageProcessor with cobertura coverage type for each test
        return CoverageProcessor("fake_path", "app.py", "cobertura")

    def test_parse_coverage_report_cobertura(self, mock_xml_tree, processor):
        """
        Tests the parse_coverage_report method for correct line number and coverage calculation with Cobertura reports.
        """
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report()

        assert covered_lines == [1], "Should list line 1 as covered"
        assert missed_lines == [2], "Should list line 2 as missed"
        assert coverage_pct == 0.5, "Coverage should be 50 percent"

    def test_correct_parsing_for_matching_package_and_class(self, mocker):
        # Setup
        mock_open = mocker.patch(
            "builtins.open",
            mocker.mock_open(
                read_data="PACKAGE,CLASS,LINE_MISSED,LINE_COVERED\ncom.example,MyClass,5,10"
            ),
        )
        mocker.patch(
            "csv.DictReader",
            return_value=[
                {
                    "PACKAGE": "com.example",
                    "CLASS": "MyClass",
                    "LINE_MISSED": "5",
                    "LINE_COVERED": "10",
                }
            ],
        )
        processor = CoverageProcessor(
            "path/to/coverage_report.csv", "path/to/MyClass.java", "jacoco"
        )

        # Action
        missed, covered = processor.parse_missed_covered_lines_jacoco(
            "com.example", "MyClass"
        )

        # Assert
        assert missed == 5
        assert covered == 10

    def test_returns_empty_lists_and_float(self, mocker):
        # Mocking the necessary methods
        mocker.patch(
            "cover_agent.CoverageProcessor.CoverageProcessor.extract_package_and_class_java",
            return_value=("com.example", "Example"),
        )
        mocker.patch(
            "cover_agent.CoverageProcessor.CoverageProcessor.parse_missed_covered_lines_jacoco",
            return_value=(0, 0),
        )

        # Initialize the CoverageProcessor object
        coverage_processor = CoverageProcessor(
            file_path="path/to/coverage.xml",
            src_file_path="path/to/example.java",
            coverage_type="jacoco",
        )

        # Invoke the parse_coverage_report_jacoco method
        lines_covered, lines_missed, coverage_percentage = (
            coverage_processor.parse_coverage_report_jacoco()
        )

        # Assert the results
        assert lines_covered == [], "Expected lines_covered to be an empty list"
        assert lines_missed == [], "Expected lines_missed to be an empty list"
        assert coverage_percentage == 0, "Expected coverage percentage to be 0"

    def test_parse_coverage_report_unsupported_type(self):
        processor = CoverageProcessor("fake_path", "app.py", "unsupported_type")
        with pytest.raises(
            ValueError, match="Unsupported coverage report type: unsupported_type"
        ):
            processor.parse_coverage_report()

    def test_parse_coverage_report_not_implemented(self):
        processor = CoverageProcessor("fake_path", "app.py", "lcov")
        with pytest.raises(
            NotImplementedError,
            match="Parsing for lcov coverage reports is not implemented yet.",
        ):
            processor.parse_coverage_report()

    def test_extract_package_and_class_java_file_error(self, mocker):
        mocker.patch("builtins.open", side_effect=FileNotFoundError("File not found"))
        processor = CoverageProcessor("fake_path", "path/to/MyClass.java", "jacoco")
        with pytest.raises(FileNotFoundError, match="File not found"):
            processor.extract_package_and_class_java()

    def test_extract_package_and_class_java(self, mocker):
        java_file_content = """
        package com.example;
    
        public class MyClass {
            // class content
        }
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=java_file_content))
        processor = CoverageProcessor("fake_path", "path/to/MyClass.java", "jacoco")
        package_name, class_name = processor.extract_package_and_class_java()
        assert (
            package_name == "com.example"
        ), "Expected package name to be 'com.example'"
        assert class_name == "MyClass", "Expected class name to be 'MyClass'"

    def test_verify_report_update_file_not_updated(self, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.getmtime", return_value=1234567.0)

        processor = CoverageProcessor("fake_path", "app.py", "cobertura")
        with pytest.raises(
            AssertionError,
            match="Fatal: The coverage report file was not updated after the test command.",
        ):
            processor.verify_report_update(1234567890)

    def test_verify_report_update_file_not_exist(self, mocker):
        mocker.patch("os.path.exists", return_value=False)

        processor = CoverageProcessor("fake_path", "app.py", "cobertura")
        with pytest.raises(
            AssertionError,
            match='Fatal: Coverage report "fake_path" was not generated.',
        ):
            processor.verify_report_update(1234567890)

    def test_process_coverage_report(self, mocker):
        mock_verify = mocker.patch(
            "cover_agent.CoverageProcessor.CoverageProcessor.verify_report_update"
        )
        mock_parse = mocker.patch(
            "cover_agent.CoverageProcessor.CoverageProcessor.parse_coverage_report",
            return_value=([], [], 0.0),
        )

        processor = CoverageProcessor("fake_path", "app.py", "cobertura")
        result = processor.process_coverage_report(1234567890)

        mock_verify.assert_called_once_with(1234567890)
        mock_parse.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"

    def test_parse_missed_covered_lines_jacoco_key_error(self, mocker):
        mock_open = mocker.patch(
            "builtins.open",
            mocker.mock_open(
                read_data="PACKAGE,CLASS,LINE_MISSED,LINE_COVERED\ncom.example,MyClass,5,10"
            ),
        )
        mocker.patch(
            "csv.DictReader",
            return_value=[
                {"PACKAGE": "com.example", "CLASS": "MyClass", "LINE_MISSED": "5"}
            ],
        )  # Missing 'LINE_COVERED'

        processor = CoverageProcessor(
            "path/to/coverage_report.csv", "path/to/MyClass.java", "jacoco"
        )

        with pytest.raises(KeyError):
            processor.parse_missed_covered_lines_jacoco("com.example", "MyClass")
