from typing import Literal, Tuple
import os
import time
import xml.etree.ElementTree as ET
from cover_agent.CustomLogger import CustomLogger


class CoverageProcessor:
    def __init__(
        self, file_path: str, filename: str, coverage_type: Literal["cobertura", "lcov"]
    ):
        """
        Initializes a CoverageProcessor object.

        Args:
            file_path (str): The path to the coverage report file.
            filename (str): The name of the file for which coverage data is being processed.
            coverage_type (Literal["cobertura", "lcov"]): The type of coverage report being processed.

        Attributes:
            file_path (str): The path to the coverage report file.
            filename (str): The name of the file for which coverage data is being processed.
            coverage_type (Literal["cobertura", "lcov"]): The type of coverage report being processed.
            logger (CustomLogger): The logger object for logging messages.

        Returns:
            None
        """
        self.file_path = file_path
        self.filename = filename
        self.coverage_type = coverage_type
        self.logger = CustomLogger.get_logger(__name__)

    def process_coverage_report(
        self, time_of_test_command: int
    ) -> Tuple[list, list, float]:
        """
        Verifies the coverage report's existence and update time, and then
        parses the report based on its type to extract coverage data.

        Args:
            time_of_test_command (int): The time the test command was run, in milliseconds.

        Returns:
            Tuple[list, list, float]: A tuple containing lists of covered and missed line numbers, and the coverage percentage.
        """
        self.verify_report_update(time_of_test_command)
        return self.parse_coverage_report()

    def verify_report_update(self, time_of_test_command: int):
        """
        Verifies the coverage report's existence and update time.

        Args:
            time_of_test_command (int): The time the test command was run, in milliseconds.

        Raises:
            AssertionError: If the coverage report does not exist or was not updated after the test command.
        """
        assert os.path.exists(
            self.file_path
        ), f'Fatal: Coverage report "{self.file_path}" was not generated.'

        # Convert file modification time to milliseconds for comparison
        file_mod_time_ms = int(round(os.path.getmtime(self.file_path) * 1000))

        assert (
            file_mod_time_ms > time_of_test_command
        ), f"Fatal: The coverage report file was not updated after the test command. file_mod_time_ms: {file_mod_time_ms}, time_of_test_command: {time_of_test_command}. {file_mod_time_ms > time_of_test_command}"

    def parse_coverage_report(self) -> Tuple[list, list, float]:
        """
        Parses a code coverage report to extract covered and missed line numbers for a specific file,
        and calculates the coverage percentage, based on the specified coverage report type.

        Returns:
            Tuple[list, list, float]: A tuple containing lists of covered and missed line numbers, and the coverage percentage.
        """
        if self.coverage_type == "cobertura":
            return self.parse_coverage_report_cobertura()
        elif self.coverage_type == "lcov":
            # Placeholder for LCOV report parsing
            raise NotImplementedError(
                f"Parsing for {self.coverage_type} coverage reports is not implemented yet."
            )
        else:
            raise ValueError(f"Unsupported coverage report type: {self.coverage_type}")

    def parse_coverage_report_cobertura(self) -> Tuple[list, list, float]:
        """
        Parses a Cobertura XML code coverage report to extract covered and missed line numbers for a specific file,
        and calculates the coverage percentage.

        Returns:
            Tuple[list, list, float]: A tuple containing lists of covered and missed line numbers, and the coverage percentage.
        """
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        lines_covered, lines_missed = [], []

        for cls in root.findall(".//class"):
            name_attr = cls.get("filename")
            if name_attr and name_attr.endswith(self.filename):
                for line in cls.findall(".//line"):
                    line_number = int(line.get("number"))
                    hits = int(line.get("hits"))
                    if hits > 0:
                        lines_covered.append(line_number)
                    else:
                        lines_missed.append(line_number)
                break  # Assuming filename is unique, break after finding and processing it

        total_lines = len(lines_covered) + len(lines_missed)
        coverage_percentage = (
            (len(lines_covered) / total_lines) if total_lines > 0 else 0
        )

        return lines_covered, lines_missed, coverage_percentage
