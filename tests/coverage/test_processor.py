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

class TestCoverageProcessorFactory:
    def test_create_processor_cobertura(self):
        processor = CoverageProcessorFactory.create_processor("cobertura", "fake_path", "app.py")
        assert isinstance(processor, CoberturaProcessor), "Expected CoberturaProcessor instance"

    def test_create_processor_jacoco(self):
        processor = CoverageProcessorFactory.create_processor("jacoco", "fake_path", "app.py")
        assert isinstance(processor, JacocoProcessor), "Expected JacocoProcessor instance"

    def test_create_processor_lcov(self):
        processor = CoverageProcessorFactory.create_processor("lcov", "fake_path", "app.py")
        assert isinstance(processor, LcovProcessor), "Expected LcovProcessor instance"

    def test_create_processor_unsupported_type(self):
        with pytest.raises(ValueError, match="Invalid coverage type specified: unsupported_type"):
            CoverageProcessorFactory.create_processor("unsupported_type", "fake_path", "app.py")

class TestCoverageProcessor:
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

class TestCoberturaProcessor:
    @pytest.fixture
    def processor(self):
        # Initializes CoberturaProcessor with cobertura coverage type for each test
        return CoverageProcessorFactory.create_processor("cobertura", "fake_path", "app.py")

    def test_parse_coverage_report_cobertura(self, mock_xml_tree, processor):
        """
        Tests the parse_coverage_report method for correct line number and coverage calculation with Cobertura reports.
        """
        coverage = processor.parse_coverage_report()
        assert len(coverage) == 1, "Expected coverage data for one file"
        assert coverage["app.py"].covered_lines == [1], "Should list line 1 as covered"
        assert coverage["app.py"].covered == 1, "Should have 1 line as covered"
        assert coverage["app.py"].missed_lines == [2], "Should list line 2 as missed"
        assert coverage["app.py"].missed == 1, "Should have 1 line as missed"
        assert coverage["app.py"].coverage == 0.5, "Coverage should be 50 percent"