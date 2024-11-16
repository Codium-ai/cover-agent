from abc import ABC, abstractmethod
from dataclasses import dataclass
from cover_agent.CustomLogger import CustomLogger
from typing import Dict, Optional, Tuple, Union
import csv
import os
import xml.etree.ElementTree as ET

@dataclass
class CoverageData:
    """
    A class to represent coverage data.

    Attributes:
        covered_lines (int): The number of lines that are covered by tests.
        missed_lines (int): The number of lines that are not covered by tests.
        coverage (float): The coverage percentage of the file or class.
    """
    covered_lines: int
    missed_lines: int
    coverage: float

@dataclass
class CoverageReport:
    """
    A class to represent the coverage report of a project.

    Attributes:
    ----------
    total_coverage : float
        The total coverage percentage of the project.
    file_coverage : Dict[str, CoverageData]
        A dictionary mapping file names to their respective coverage data.
    """
    total_coverage: float
    file_coverage: Dict[str, CoverageData]

class CoverageProcessor(ABC):
    """
    Abstract base class for processing coverage reports.

    Attributes:
        file_path (str): The path to the coverage report file.
        src_file_path (str): The path to the source file.
        logger (Logger): The logger object for logging messages.
    Methods:
        parse_coverage_report() -> Union[Tuple[list, list, float], dict]:
            Abstract method to parse the coverage report.
        
        process_coverage_report(time_of_test_command: int) -> Union[Tuple[list, list, float], dict]:
            Processes the coverage report and returns the coverage data.
        
        _is_report_exist():
            Checks if the coverage report file exists.
        
        _is_report_obsolete(time_of_test_command: int):
            Checks if the coverage report file is obsolete based on the test command time.
    """
    def __init__(
        self,
        file_path: str,
        src_file_path: str,
    ):
        self.file_path = file_path
        self.src_file_path = src_file_path
        self.logger = CustomLogger.get_logger(__name__)

    @abstractmethod
    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        pass
    
    @abstractmethod
    def process_coverage_report(self, time_of_test_command: int) -> CoverageReport:
        self._is_coverage_valid(time_of_test_command=int(os.path.getmtime(self.file_path) * 1000))
        coverage = self.parse_coverage_report()
        report = CoverageReport(0.0, coverage)
        if coverage:
            total_covered_lines = sum(cov.covered_lines for cov in coverage.file_coverage.values())
            total_missed_lines = sum(cov.missed_lines for cov in coverage.file_coverage.values())
            total_lines = total_covered_lines + total_missed_lines
            report.total_coverage = (float(total_covered_lines) / total_lines) if total_lines > 0 else 0.0
        return report

    def _is_coverage_valid(
        self, time_of_test_command: int
    ) ->  None:
        self._is_report_exist()
        self._is_report_obsolete(time_of_test_command)

    def _is_report_exist(self):
       if not os.path.exists(self.file_path):
            raise FileNotFoundError(f'Coverage report "{self.file_path}" not found')

    def _is_report_obsolete(self, time_of_test_command: int):
       if int(os.path.getmtime(self.file_path) * 1000) <= time_of_test_command:
            raise ValueError("Coverage report is outdated")
    
class CoberturaProcessor(CoverageProcessor):
    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        self._is_coverage_valid(time_of_test_command=int(os.path.getmtime(self.file_path) * 1000))

        tree = ET.parse(self.file_path)
        root = tree.getroot()
        coverage = Dict[str, CoverageData]
        for cls in root.findall(".//class"):
            cls_filename = cls.get("filename")
            if cls_filename:
                coverage[cls_filename] = self._parse_coverage_data_for_class(cls)
        return coverage

    def _parse_coverage_data_for_class(self, cls) -> CoverageData:
        lines_covered, lines_missed = [], []
        for line in cls.findall(".//line"):
            line_number = int(line.get("number"))
            hits = int(line.get("hits"))
            if hits > 0:
                lines_covered.append(line_number)
            else:
                lines_missed.append(line_number)
        total_lines = len(lines_covered) + len(lines_missed)
        coverage_percentage = (float(lines_covered) / total_lines) if total_lines > 0 else 0.0
        return CoverageData(lines_covered, lines_missed, coverage_percentage)

class LcovProcessor(CoverageProcessor):
    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        coverage = {}
        try:
            with open(self.file_path, "r") as file:
                for line in file:
                    line = line.strip()
                    if line.startswith("SF:"):
                        filename = line[3:]
                        lines_covered, lines_missed = [], []
                        for line in file:
                            line = line.strip()
                            if line.startswith("DA:"):
                                line_number, hits = map(int, line[3:].split(","))
                                if hits > 0:
                                    lines_covered.append(int(line_number))
                                else:
                                    lines_missed.append(int(line_number))
                            elif line.startswith("end_of_record"):
                                break
                        total_lines = len(lines_covered) + len(lines_missed)
                        coverage_percentage = (float(lines_covered) / total_lines) if total_lines > 0 else 0.0
                        coverage[filename] = CoverageData(lines_covered, lines_missed, coverage_percentage)
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error reading file {self.file_path}: {e}")
            raise
        return coverage

class JacocoProcessor(CoverageProcessor):
    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        coverage = {}
        file_extension = self._get_file_extension(self.file_path)
        if file_extension == 'xml':
            coverage = self._parse_jacoco_xml()
        elif file_extension == 'csv':
            coverage = self._parse_jacoco_csv()
        else:
            raise ValueError(f"Unsupported JaCoCo code coverage report format: {file_extension}")
        return coverage
    
    def _get_file_extension(self, filename: str) -> str | None:
        """Get the file extension from a given filename."""
        return os.path.splitext(filename)[1].lstrip(".")
    
    def _parse_jacoco_xml(self) -> Dict[str, CoverageData]:
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        coverage = {}
        for sourcefile in root.findall(".//sourcefile"):
            filename = sourcefile.get("name")
            missed, covered = 0, 0
            for counter in sourcefile.findall('counter'):
                if counter.attrib.get('type') == 'LINE':
                    missed = int(counter.attrib.get('missed', 0))
                    covered = int(counter.attrib.get('covered', 0))
                    break
            total_lines = missed + covered
            coverage_percentage = (float(covered) / total_lines) if total_lines > 0 else 0
            coverage[filename] = CoverageData(covered, missed, coverage_percentage)
        return coverage
    def _parse_jacoco_csv(self) -> Dict[str, CoverageData]:
        coverage = {}
        with open(self.file_path, "r") as file:
            reader = csv.DictReader(file)
            missed, covered = 0, 0
            for row in reader:
                try:
                    missed = int(row["LINE_MISSED"])
                    covered = int(row["LINE_COVERED"])
                    total_lines = missed + covered
                    coverage_percentage = (float(covered) / total_lines) if total_lines > 0 else 0
                    coverage[filename] = CoverageData(covered, missed, coverage_percentage)
                    break
                except KeyError as e:
                    self.logger.error("Missing expected column in CSV: {e}")
                    raise
        return coverage

class CoverageReportFilter:
    def filter_report(self, report: CoverageReport, file_pattern: str) -> CoverageReport:
        filtered_coverage = {
            file: coverage 
            for file, coverage in report.file_coverage.items()
            if file_pattern in file
        }
        return CoverageReport(
            total_coverage=sum(cov.covered_lines for cov in filtered_coverage.values()) / 
                         sum(cov.covered_lines + cov.missed_lines for cov in filtered_coverage.values())
                         if filtered_coverage else 0.0,
            file_coverage=filtered_coverage
        )

class CoverageProcessorFactory:
    """Factory for creating coverage processors based on tool type."""
    
    @staticmethod
    def create_processor(
        tool_type: str,
        report_path: str, 
        src_file_path: str
    ) -> CoverageProcessor:
        """
        Creates appropriate coverage processor instance.
        
        Args:
            tool_type: Coverage tool type (cobertura/jacoco/lcov)
            report_path: Path to coverage report
            src_file_path: Path to source file
            
        Returns:
            CoverageProcessor instance
            
        Raises:
            ValueError: If invalid tool type specified
        """
        processors = {
            'cobertura': CoberturaProcessor,
            'jacoco': JacocoProcessor,
            'lcov': LcovProcessor
        }
        if tool_type.lower() not in processors:
            raise ValueError(f"Invalid coverage type specified: {tool_type}")
        return processors[tool_type.lower()](report_path, src_file_path)

def process_coverage(
    tool_type: str,
    report_path: str,
    src_file_path: str,
    is_global_coverage_enabled: bool = True,
    file_pattern: Optional[str] = None
) -> CoverageReport:
    # Create appropriate processor
    processor = CoverageProcessorFactory.create_processor(tool_type, report_path, src_file_path)
    
    # Process full report
    report = processor.parse_coverage_report()
    
    # Apply filtering if needed
    if not is_global_coverage_enabled and file_pattern:
        filter = CoverageReportFilter()
        report = filter.filter_report(report, file_pattern)
        
    return report