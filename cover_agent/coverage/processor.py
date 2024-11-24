from abc import ABC, abstractmethod
from dataclasses import dataclass
from cover_agent.CustomLogger import CustomLogger
from typing import Dict, Optional, List, Tuple, Union
import csv
import os
import re
import xml.etree.ElementTree as ET

@dataclass(frozen=True)
class CoverageData:
    """
    A class to represent coverage data.

    Attributes:
        covered_lines (int): The line numbers that are covered by tests.
        covered (int)      : The number of lines that are covered by tests.
        missed_lines (int) : The line nubmers that are not covered by tests.
        missed (int)       : The number of lines that are not covered by tests.
        coverage (float)   : The coverage percentage of the file or class.
    """
    covered_lines: List[int]
    covered: int
    missed_lines: List[int]
    missed: int
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
    
    def process_coverage_report(self, time_of_test_command: int) -> CoverageReport:
        self._is_coverage_valid(time_of_test_command=time_of_test_command)
        coverage = self.parse_coverage_report()
        report = CoverageReport(0.0, coverage)
        if coverage:
            total_covered = sum(cov.covered for cov in coverage.values())
            total_missed = sum(cov.missed for cov in coverage.values())
            total_lines = total_covered + total_missed
            report.total_coverage = (float(total_covered) / float(total_lines)) if total_lines > 0 else 0.0
        return report

    def _is_coverage_valid(
        self, time_of_test_command: int
    ) ->  None:
        if not self._is_report_exist():
            raise FileNotFoundError(f'Coverage report "{self.file_path}" not found')
        if self._is_report_obsolete(time_of_test_command):
            raise ValueError("Coverage report is outdated")

    def _is_report_exist(self) -> bool:
        return os.path.exists(self.file_path)

    def _is_report_obsolete(self, time_of_test_command: int) -> bool:
        return int(round(os.path.getmtime(self.file_path) * 1000)) < time_of_test_command
    
class CoberturaProcessor(CoverageProcessor):
    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        coverage = {}
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
        coverage_percentage = (float(len(lines_covered)) / total_lines) if total_lines > 0 else 0.0
        return CoverageData(lines_covered, len(lines_covered), lines_missed, len(lines_missed), coverage_percentage)

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
                        coverage_percentage = (float(len(lines_covered)) / total_lines) if total_lines > 0 else 0.0
                        coverage[filename] = CoverageData(lines_covered, len(lines_covered), lines_missed, len(lines_missed), coverage_percentage)
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error reading file {self.file_path}: {e}")
            raise
        return coverage

class JacocoProcessor(CoverageProcessor):
    def parse_coverage_report(self) -> Dict[str, CoverageData]:
        coverage = {}
        package_name, class_name = self._extract_package_and_class_java()
        file_extension = self._get_file_extension(self.file_path)
        if file_extension == 'xml':
            missed, covered = self._parse_jacoco_xml(class_name=class_name)
        elif file_extension == 'csv':
            missed, covered = self._parse_jacoco_csv(package_name=package_name, class_name=class_name)
        else:
            raise ValueError(f"Unsupported JaCoCo code coverage report format: {file_extension}")
        total_lines = missed + covered
        coverage_percentage = (float(covered) / total_lines) if total_lines > 0 else 0.0
        coverage[class_name] = CoverageData(covered=covered, missed=missed, coverage_percentag=coverage_percentage)
        return coverage
    
    def _get_file_extension(self, filename: str) -> str | None:
        """Get the file extension from a given filename."""
        return os.path.splitext(filename)[1].lstrip(".")
    
    def _extract_package_and_class_java(self):
        package_pattern = re.compile(r"^\s*package\s+([\w\.]+)\s*;.*$")
        class_pattern = re.compile(r"^\s*public\s+class\s+(\w+).*")

        package_name = ""
        class_name = ""
        try:
            with open(self.src_file_path, "r") as file:
                for line in file:
                    if not package_name:  # Only match package if not already found
                        package_match = package_pattern.match(line)
                        if package_match:
                            package_name = package_match.group(1)

                    if not class_name:  # Only match class if not already found
                        class_match = class_pattern.match(line)
                        if class_match:
                            class_name = class_match.group(1)

                    if package_name and class_name:  # Exit loop if both are found
                        break
        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error reading file {self.src_file_path}: {e}")
            raise

        return package_name, class_name
    
    def _parse_jacoco_xml(
        self, class_name: str
    ) -> tuple[int, int]:
        """Parses a JaCoCo XML code coverage report to extract covered and missed line numbers for a specific file."""
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        sourcefile = root.find(f".//sourcefile[@name='{class_name}.java']")

        if sourcefile is None:
            return 0, 0

        missed, covered = 0, 0
        for counter in sourcefile.findall('counter'):
            if counter.attrib.get('type') == 'LINE':
                missed += int(counter.attrib.get('missed', 0))
                covered += int(counter.attrib.get('covered', 0))
                break

        return missed, covered
    def _parse_jacoco_csv(self, package_name, class_name) -> Dict[str, CoverageData]:
        with open(self.file_path, "r") as file:
            reader = csv.DictReader(file)
            missed, covered = 0, 0
            for row in reader:
                if row["PACKAGE"] == package_name and row["CLASS"] == class_name:
                    try:
                        missed = int(row["LINE_MISSED"])
                        covered = int(row["LINE_COVERED"])
                        break
                    except KeyError as e:
                        self.logger.error(f"Missing expected column in CSV: {e}")
                        raise

        return missed, covered

class CoverageReportFilter:
    def filter_report(self, report: CoverageReport, file_pattern: str) -> CoverageReport:
        filtered_coverage = {
            file: coverage 
            for file, coverage in report.file_coverage.items()
            if file_pattern in file
        }
        return CoverageReport(
            total_coverage=(sum(cov.covered_lines for cov in filtered_coverage.values()) / 
                         sum(cov.covered_lines + cov.missed_lines for cov in filtered_coverage.values()))
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
    report = processor.process_coverage_report(time_of_test_command=int(os.path.getmtime(report_path) * 1000))
    
    # Apply filtering if needed
    if not is_global_coverage_enabled and file_pattern:
        filter = CoverageReportFilter()
        report = filter.filter_report(report, file_pattern)
        
    return report