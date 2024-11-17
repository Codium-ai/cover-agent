import pytest
import xml.etree.ElementTree as ET
from cover_agent.coverage.processor import (
    CoverageProcessor,
    CoverageProcessorFactory,
    JacocoProcessor,
    CoberturaProcessor,
    LcovProcessor,
    CoverageData
)


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
        return CoverageProcessorFactory.create_processor("cobertura", "fake_path", "app.py")

    def test_parse_coverage_report_cobertura(self, mock_xml_tree, processor):
        """
        Tests the parse_coverage_report method for correct line number and coverage calculation with Cobertura reports.
        """
        coverage = processor.parse_coverage_report()
        assert len(coverage) == 1, "Expected coverage data for one file"
        assert coverage["app.py"].covered_lines == 1, "Should list line 1 as covered"
        assert coverage["app.py"].missed_lines == 1, "Should list line 2 as missed"
        assert coverage["app.py"].coverage == 0.5, "Coverage should be 50 percent"

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
        processor = CoverageProcessorFactory.create_processor(
             "jacoco", "path/to/coverage_report.csv", "path/to/MyClass.java"
        )

        # Action
        missed, covered = processor._parse_jacoco_csv(
            "com.example", "MyClass"
        )

        # Assert
        assert missed == 5
        assert covered == 10

    def test_returns_empty_lists_and_float(self, mocker):
        # Mocking the necessary methods
        mocker.patch(
            "cover_agent.coverage.processor.JacocoProcessor._extract_package_and_class_java",
            return_value=("com.example", "Example"),
        )
        mocker.patch(
            "cover_agent.coverage.processor.JacocoProcessor._parse_jacoco_xml",
            return_value=(0, 0),
        )

        # Initialize the CoverageProcessor object
        coverage_processor = CoverageProcessorFactory.create_processor(
            "jacoco",
            "path/to/coverage.xml",
            "path/to/example.java"
        )

        # Invoke the parse_coverage_report_jacoco method
        coverage = (
            coverage_processor.parse_coverage_report()
        )

        # Assert the results
        assert len(coverage) == 1, "Expected coverage data for one file"
        assert coverage["Example"].covered_lines == 0, "Expected lines_covered to be an empty list"
        assert coverage["Example"].missed_lines == 0, "Expected lines_missed to be an empty list"
        assert coverage["Example"].coverage == 0.0, "Expected coverage percentage to be 0"

    def test_parse_coverage_report_unsupported_type(self):
        with pytest.raises(
            ValueError, match="Unsupported coverage report type: unsupported_type"
        ):
            processor = CoverageProcessorFactory.create_processor(
                "unsupported_format", "path/to/coverage_report.csv", "path/to/MyClass.java"
            )

    def test_extract_package_and_class_java_file_error(self, mocker):
        mocker.patch("builtins.open", side_effect=FileNotFoundError("File not found"))
        processor = CoverageProcessorFactory.create_processor(
             "jacoco", "path/to/coverage_report.csv", "path/to/MyClass.java"
        )
        with pytest.raises(FileNotFoundError, match="File not found"):
            processor._extract_package_and_class_java()

    def test_extract_package_and_class_java(self, mocker):
        java_file_content = """
        package com.example;
    
        public class MyClass {
            // class content
        }
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=java_file_content))
        processor = CoverageProcessorFactory.create_processor(
             "jacoco", "path/to/coverage_report.csv", "path/to/MyClass.java"
        )
        package_name, class_name = processor._extract_package_and_class_java()
        assert (
            package_name == "com.example"
        ), "Expected package name to be 'com.example'"
        assert class_name == "MyClass", "Expected class name to be 'MyClass'"

    def test_is_report_obsolete(self, mocker):
        mocker.patch("os.path.exists", return_value=True)
        mocker.patch("os.path.getmtime", return_value=1234567.0)
        processor = CoverageProcessorFactory.create_processor(
             "cobertura", "fake_path", "app.py"
        )
        with pytest.raises(
            ValueError,
            match="Coverage report is outdated",
        ):
            processor._is_coverage_valid(1234567890)

    def test_is_report_exist(self, mocker):
        mocker.patch("os.path.exists", return_value=False)

        processor = CoverageProcessorFactory.create_processor(
             "cobertura", "fake_path", "app.py"
        )
        with pytest.raises(
            FileNotFoundError,
            match='Coverage report "fake_path" not found',
        ):
            processor._is_coverage_valid(1234567890)

    def test_process_coverage_report(self, mocker):
        mock_verify_report_obsolete = mocker.patch(
            "cover_agent.coverage.processor.CoverageProcessor._is_report_obsolete"
        )
        mock_verify_report_exists = mocker.patch(
            "cover_agent.coverage.processor.CoverageProcessor._is_report_exist"
        )
        mock_parse = mocker.patch(
            "cover_agent.coverage.processor.JacocoProcessor.parse_coverage_report",
            return_value=([], [], 0.0),
        )

        processor = CoverageProcessorFactory.create_processor(
             "cobertura", "fake_path", "app.py"
        )
        result = processor.process_coverage_report(1234567890)

        mock_verify_report_obsolete.assert_called_once_with(1234567890)
        mock_verify_report_exists.assert_called_once()
        mock_parse.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"

    def test_parse_missed_covered_lines_jacoco_csv_key_error(self, mocker):
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

        processor = CoverageProcessorFactory.create_processor(
             "jacoco", "path/to/coverage_report.csv", "path/to/MyClass.java"
        )

        with pytest.raises(KeyError):
            processor._parse_jacoco_csv("com.example", "MyClass")

    def test_parse_coverage_report_lcov_no_coverage_data(self, mocker):
        """
        Test parse_coverage_report_lcov returns empty lists and 0 coverage when the lcov report contains no relevant data.
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=""))
        processor = CoverageProcessor("empty_report.lcov", "app.py", "lcov")
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report_lcov()
        assert covered_lines == [], "Expected no covered lines"
        assert missed_lines == [], "Expected no missed lines"
        assert coverage_pct == 0, "Expected 0% coverage"

    def test_parse_coverage_report_lcov_with_coverage_data(self, mocker):
        """
        Test parse_coverage_report_lcov correctly parses coverage data from an lcov report.
        """
        lcov_data = """
        SF:app.py
        DA:1,1
        DA:2,0
        DA:3,1
        end_of_record
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=lcov_data))
        processor = CoverageProcessor("report.lcov", "app.py", "lcov")
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report_lcov()
        assert covered_lines == [1, 3], "Expected lines 1 and 3 to be covered"
        assert missed_lines == [2], "Expected line 2 to be missed"
        assert coverage_pct == 2/3, "Expected 66.67% coverage"

    def test_parse_coverage_report_lcov_with_multiple_files(self, mocker):
        """
        Test parse_coverage_report_lcov correctly parses coverage data for the target file among multiple files in the lcov report.
        """
        lcov_data = """
        SF:other.py
        DA:1,1
        DA:2,0
        end_of_record
        SF:app.py
        DA:1,1
        DA:2,0
        DA:3,1
        end_of_record
        SF:another.py
        DA:1,1
        end_of_record
        """
        mocker.patch("builtins.open", mocker.mock_open(read_data=lcov_data))
        processor = CoverageProcessor("report.lcov", "app.py", "lcov")
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report_lcov()
        assert covered_lines == [1, 3], "Expected lines 1 and 3 to be covered for app.py"
        assert missed_lines == [2], "Expected line 2 to be missed for app.py"
        assert coverage_pct == 2/3, "Expected 66.67% coverage for app.py"

    def test_parse_coverage_report_unsupported_type(self, mocker):
        mocker.patch(
            "cover_agent.CoverageProcessor.CoverageProcessor.extract_package_and_class_java",
            return_value=("com.example", "Example"),
        )

        processor = CoverageProcessor(
            "path/to/coverage_report.html", "path/to/MyClass.java", "jacoco"
        )
        with pytest.raises(
            ValueError, match="Unsupported JaCoCo code coverage report format: html"
        ):
            processor.parse_coverage_report_jacoco()

    def test_parse_missed_covered_lines_jacoco_xml_no_source_file(self, mocker):
        #, mock_xml_tree
        mocker.patch(
            "cover_agent.CoverageProcessor.CoverageProcessor.extract_package_and_class_java",
            return_value=("com.example", "Example"),
        )

        xml_str = """<report>
                        <package name="path/to">
                            <sourcefile name="MyClass.java">
                                <counter type="INSTRUCTION" missed="53" covered="387"/>
                                <counter type="BRANCH" missed="2" covered="6"/>
                                <counter type="LINE" missed="9" covered="94"/>
                                <counter type="COMPLEXITY" missed="5" covered="23"/>
                                <counter type="METHOD" missed="3" covered="21"/>
                                <counter type="CLASS" missed="0" covered="1"/>
                            </sourcefile>
                        </package>
                    </report>"""

        mocker.patch(
            "xml.etree.ElementTree.parse",
            return_value=ET.ElementTree(ET.fromstring(xml_str))
        )

        processor = CoverageProcessor(
            "path/to/coverage_report.xml", "path/to/MySecondClass.java", "jacoco"
        )

        # Action
        missed, covered = processor.parse_missed_covered_lines_jacoco_xml(
            "MySecondClass"
        )

        # Assert
        assert missed == 0
        assert covered == 0

    def test_parse_missed_covered_lines_jacoco_xml(self, mocker):
        #, mock_xml_tree
        mocker.patch(
            "cover_agent.CoverageProcessor.CoverageProcessor.extract_package_and_class_java",
            return_value=("com.example", "Example"),
        )

        xml_str = """<report>
                        <package name="path/to">
                            <sourcefile name="MyClass.java">
                                <counter type="INSTRUCTION" missed="53" covered="387"/>
                                <counter type="BRANCH" missed="2" covered="6"/>
                                <counter type="LINE" missed="9" covered="94"/>
                                <counter type="COMPLEXITY" missed="5" covered="23"/>
                                <counter type="METHOD" missed="3" covered="21"/>
                                <counter type="CLASS" missed="0" covered="1"/>
                            </sourcefile>
                        </package>
                    </report>"""

        mocker.patch(
            "xml.etree.ElementTree.parse",
            return_value=ET.ElementTree(ET.fromstring(xml_str))
        )

        processor = CoverageProcessor(
            "path/to/coverage_report.xml", "path/to/MyClass.java", "jacoco"
        )

        # Action
        missed, covered = processor.parse_missed_covered_lines_jacoco_xml(
            "MyClass"
        )

        # Assert
        assert missed == 9
        assert covered == 94

    def test_get_file_extension_with_valid_file_extension(self):
        processor = CoverageProcessor(
            "path/to/coverage_report.xml", "path/to/MyClass.java", "jacoco"
        )

        file_extension = processor.get_file_extension("coverage_report.xml")

        # Assert
        assert file_extension == 'xml'

    def test_get_file_extension_with_no_file_extension(self):
        processor = CoverageProcessor(
            "path/to/coverage_report", "path/to/MyClass.java", "jacoco"
        )

        file_extension = processor.get_file_extension("coverage_report")

        # Assert
        assert file_extension is ''

    def test_parse_coverage_report_lcov_with_feature_flag(self, mocker):
        mock_parse_lcov = mocker.patch("cover_agent.CoverageProcessor.CoverageProcessor.parse_coverage_report_lcov", return_value=([], [], 0.0))
        processor = CoverageProcessor("fake_path", "app.py", "lcov", use_report_coverage_feature_flag=True)
        result = processor.parse_coverage_report()
        mock_parse_lcov.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"


    def test_parse_coverage_report_cobertura_with_feature_flag(self, mocker):
        mock_parse_cobertura = mocker.patch("cover_agent.CoverageProcessor.CoverageProcessor.parse_coverage_report_cobertura", return_value=([], [], 0.0))
        processor = CoverageProcessor("fake_path", "app.py", "cobertura", use_report_coverage_feature_flag=True)
        result = processor.parse_coverage_report()
        mock_parse_cobertura.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"


    def test_parse_coverage_report_jacoco(self, mocker):
        mock_parse_jacoco = mocker.patch("cover_agent.CoverageProcessor.CoverageProcessor.parse_coverage_report_jacoco", return_value=([], [], 0.0))
        processor = CoverageProcessor("fake_path", "app.py", "jacoco", use_report_coverage_feature_flag=True)
        result = processor.parse_coverage_report()
        mock_parse_jacoco.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"


    def test_parse_coverage_report_cobertura_filename_not_found(self, mock_xml_tree, processor):
        covered_lines, missed_lines, coverage_pct = processor.parse_coverage_report_cobertura("non_existent_file.py")
        assert covered_lines == [], "Expected no covered lines"
        assert missed_lines == [], "Expected no missed lines"
        assert coverage_pct == 0.0, "Expected 0% coverage"


    def test_parse_coverage_report_lcov_file_read_error(self, mocker):
        mocker.patch("builtins.open", side_effect=IOError("File read error"))
        processor = CoverageProcessor("report.lcov", "app.py", "lcov")
        with pytest.raises(IOError, match="File read error"):
            processor.parse_coverage_report_lcov()


    def test_parse_coverage_report_cobertura_all_files(self, mock_xml_tree, processor):
        coverage_data = processor.parse_coverage_report_cobertura()
        expected_data = {
            "app.py": ([1], [2], 0.5)
        }
        assert coverage_data == expected_data, "Expected coverage data for all files"


    def test_parse_coverage_report_unsupported_type_with_feature_flag(self):
        processor = CoverageProcessor("fake_path", "app.py", "unsupported_type", use_report_coverage_feature_flag=True)
        with pytest.raises(ValueError, match="Unsupported coverage report type: unsupported_type"):
            processor.parse_coverage_report()

    def test_parse_coverage_report_jacoco_without_feature_flag(self, mocker):
        mock_parse_jacoco = mocker.patch(
            "cover_agent.CoverageProcessor.CoverageProcessor.parse_coverage_report_jacoco",
            return_value=([], [], 0.0)
        )
        processor = CoverageProcessor("fake_path", "app.py", "jacoco", use_report_coverage_feature_flag=False)
        result = processor.parse_coverage_report()
        mock_parse_jacoco.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"

    def test_parse_coverage_report_unsupported_type_without_feature_flag(self):
        processor = CoverageProcessor("fake_path", "app.py", "unsupported_type", use_report_coverage_feature_flag=False)
        with pytest.raises(ValueError, match="Unsupported coverage report type: unsupported_type"):
            processor.parse_coverage_report()



    def test_parse_coverage_report_lcov_without_feature_flag(self, mocker):
        mock_parse_lcov = mocker.patch(
            "cover_agent.CoverageProcessor.CoverageProcessor.parse_coverage_report_lcov",
            return_value=([], [], 0.0)
        )
        processor = CoverageProcessor("fake_path", "app.py", "lcov", use_report_coverage_feature_flag=False)
        result = processor.parse_coverage_report()
        mock_parse_lcov.assert_called_once()
        assert result == ([], [], 0.0), "Expected result to be ([], [], 0.0)"
