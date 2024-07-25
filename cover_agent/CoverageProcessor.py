from typing import Literal, Tuple
import os
import time
import re
import csv
import xml.etree.ElementTree as ET
from cover_agent.CustomLogger import CustomLogger


class CoverageProcessor:
    def __init__(
        self,
        file_path: str,
        src_file_path: str,
        coverage_type: Literal["cobertura", "lcov", "jacoco"],
    ):
        """
        Initializes a CoverageProcessor object.

        Args:
            file_path (str): The path to the coverage report file.
            src_file_path (str): The fully qualified path of the file for which coverage data is being processed.
            coverage_type (Literal["cobertura", "lcov"]): The type of coverage report being processed.

        Attributes:
            file_path (str): The path to the coverage report file.
            src_file_path (str): The fully qualified path of the file for which coverage data is being processed.
            coverage_type (Literal["cobertura", "lcov"]): The type of coverage report being processed.
            logger (CustomLogger): The logger object for logging messages.

        Returns:
            None
        """
        self.file_path = file_path
        self.src_file_path = src_file_path
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
            return self.parse_coverage_report_lcov()
        elif self.coverage_type == "jacoco":
            return self.parse_coverage_report_jacoco()
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
        filename = os.path.basename(self.src_file_path)

        for cls in root.findall(".//class"):
            name_attr = cls.get("filename")
            if name_attr and name_attr.endswith(filename):
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

    def parse_coverage_report_lcov(self):

        lines_covered, lines_missed = [], []
        filename = os.path.basename(self.src_file_path)
        try: 
            with open(self.file_path, "r") as file:
                for line in file:
                    line = line.strip()
                    if line.startswith("SF:"):
                        if line.endswith(filename):
                            for line in file:
                                line = line.strip()
                                if line.startswith("DA:"):
                                    line_number = line.replace("DA:", "").split(",")[0]
                                    hits = line.replace("DA:", "").split(",")[1]
                                    if int(hits) > 0:
                                        lines_covered.append(int(line_number))
                                    else:
                                        lines_missed.append(int(line_number))
                                elif line.startswith("end_of_record"):
                                    break

        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error reading file {self.file_path}: {e}")
            raise

        total_lines = len(lines_covered) + len(lines_missed)
        coverage_percentage = (
            (len(lines_covered) / total_lines) if total_lines > 0 else 0
        )

        return lines_covered, lines_missed, coverage_percentage

    def parse_coverage_report_jacoco(self) -> Tuple[list, list, float]:
        """
        Parses a JaCoCo XML code coverage report to extract covered and missed line numbers for a specific file,
        and calculates the coverage percentage.

        Returns: Tuple[list, list, float]: A tuple containing empty lists of covered and missed line numbers,
        and the coverage percentage. The reason being the format of the report for jacoco gives the totals we do not
        sum them up. to stick with the current contract of the code and to do little change returning empty arrays.
        I expect this should bring up a discussion on introduce a factory for different CoverageProcessors. Where the
        total coverage percentage is returned to be evaluated only.
        """
        lines_covered, lines_missed = [], []

        package_name, class_name = self.extract_package_and_class_java()
        missed, covered = self.parse_missed_covered_lines_jacoco(
            package_name, class_name
        )

        total_lines = missed + covered
        coverage_percentage = (float(covered) / total_lines) if total_lines > 0 else 0

        return lines_covered, lines_missed, coverage_percentage

    def parse_missed_covered_lines_jacoco(
        self, package_name: str, class_name: str
    ) -> tuple[int, int]:
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
                        self.logger.error("Missing expected column in CSV: {e}")
                        raise

        return missed, covered

    def extract_package_and_class_java(self):
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
