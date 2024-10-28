from cover_agent.CustomLogger import CustomLogger
from typing import Literal, Tuple, Union
import csv
import os
import re
import xml.etree.ElementTree as ET


class CoverageProcessor:
    def __init__(
        self,
        file_path: str,
        src_file_path: str,
        coverage_type: Literal["cobertura", "lcov", "jacoco"],
        use_report_coverage_feature_flag: bool = False,
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
        self.use_report_coverage_feature_flag = use_report_coverage_feature_flag

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
            if self.use_report_coverage_feature_flag:
                if self.coverage_type == "cobertura":
                    return self.parse_coverage_report_cobertura()
                elif self.coverage_type == "lcov":
                    return self.parse_coverage_report_lcov()
                elif self.coverage_type == "jacoco":
                    return self.parse_coverage_report_jacoco()
                else:
                    raise ValueError(f"Unsupported coverage report type: {self.coverage_type}")
            else:
                if self.coverage_type == "cobertura":
                    # Default behavior is to parse out a single file from the report
                    return self.parse_coverage_report_cobertura(filename=os.path.basename(self.src_file_path))
                elif self.coverage_type == "lcov":
                    return self.parse_coverage_report_lcov()
                elif self.coverage_type == "jacoco":
                    return self.parse_coverage_report_jacoco()
                else:
                    raise ValueError(f"Unsupported coverage report type: {self.coverage_type}")

    def parse_coverage_report_cobertura(self, filename: str = None) -> Union[Tuple[list, list, float], dict]:
        """
        Parses a Cobertura XML code coverage report to extract covered and missed line numbers for a specific file
        or all files, and calculates the coverage percentage.

        Args:
            filename (str, optional): The name of the file to process. If None, processes all files.

        Returns:
            Union[Tuple[list, list, float, float], dict]: If filename is provided, returns a tuple 
                containing lists of covered and missed line numbers, the line coverage percentage,
                and the branch coverage percentage. If filename is None, returns a dictionary with 
                filenames as keys and a tuple containing lists of covered and missed line numbers, 
                and the coverage percentage as values.
        """
        tree = ET.parse(self.file_path)
        root = tree.getroot()

        if filename:
            for cls in root.findall(".//class"):
                name_attr = cls.get("filename")
                if name_attr and name_attr.endswith(filename):
                    return self.parse_coverage_data_for_class(cls)
            return [], [], 0.0, 0.0  # Return empty lists if the file is not found
        else:
            coverage_data = {}
            for cls in root.findall(".//class"):
                cls_filename = cls.get("filename")
                if cls_filename:
                    lines_covered, lines_missed, line_coverage_percentage, branch_coverage_percentage = self.parse_coverage_data_for_class(cls)
                    coverage_data[cls_filename] = (lines_covered, lines_missed, line_coverage_percentage, branch_coverage_percentage)
            self.logger.debug(f"Coverage data for all files: {coverage_data}")
            return coverage_data

    def parse_coverage_data_for_class(self, cls) -> Tuple[list, list, float, float]:
        """
        Parses coverage data for a specific class element.

        Args:
            cls (Element): The class element from the Cobertura XML.

        Returns:
            Tuple[list, list, float, float]: Lists of covered and missed line numbers, 
            the line coverage percentage, and the branch coverage percentage.
        """
        lines_covered = []
        lines_missed = []
        branches_covered = 0
        total_branches = 0

        for line in cls.findall(".//line"):
            line_number = int(line.get("number"))
            hits = int(line.get("hits"))
            if hits > 0:
                lines_covered.append(line_number)
            else:
                lines_missed.append(line_number)

            branch_rate = line.get("branch")
            if branch_rate:
                condition_coverage = line.get('condition-coverage')
                covered, total = map(int, condition_coverage.split('(')[1].split(')')[0].split('/'))
                total_branches += total
                branches_covered += covered
        
        line_coverage_percentage = len(lines_covered) / (len(lines_covered) + len(lines_missed)) if (len(lines_covered) + len(lines_missed)) > 0 else 0.0
        branch_coverage_percentage = branches_covered / total_branches if total_branches > 0 else 0.0

        return lines_covered, lines_missed, line_coverage_percentage, branch_coverage_percentage

    def parse_coverage_report_lcov(self):
        """
        Parses an LCOV code coverage report to extract covered and missed line numbers,
        branch coverage for a specific file, and calculates the coverage percentage.

        Returns:
            Tuple[list, list, float, float]: Lists of covered and missed line numbers,
            the line coverage percentage, and the branch coverage percentage.
        """
        lines_covered, lines_missed = [], []
        branches_covered, branches_missed = 0, 0
        total_branches = 0
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
                                elif line.startswith("BRDA:"):
                                    parts = line.replace("BRDA:", "").split(",")
                                    branch_hits = parts[3]
                                    total_branches += 1
                                    if branch_hits != '-' and int(branch_hits) > 0:
                                        branches_covered += 1
                                elif line.startswith("end_of_record"):
                                    break

        except (FileNotFoundError, IOError) as e:
            self.logger.error(f"Error reading file {self.file_path}: {e}")
            raise

        total_lines = len(lines_covered) + len(lines_missed)
        line_coverage_percentage = (
            (len(lines_covered) / total_lines) if total_lines > 0 else 0
        )
        branch_coverage_percentage = (
            (branches_covered / total_branches) if total_branches > 0 else 0
        )

        return lines_covered, lines_missed, line_coverage_percentage, branch_coverage_percentage

    
    def parse_coverage_report_jacoco(self) -> Tuple[list, list, float, float]:
        """
        Parses a JaCoCo XML or CSV code coverage report to extract covered and missed line numbers,
        branch coverage for a specific file, and calculates the coverage percentage.

        Returns:
            Tuple[list, list, float, float]: A tuple containing empty lists of covered and missed line numbers,
            the line coverage percentage, and the branch coverage percentage. The reason being the format of the report
            for JaCoCo gives the totals we do not sum them up. To stick with the current contract of the code and to do
            little change returning empty arrays. I expect this should bring up a discussion on introducing a factory for
            different CoverageProcessors. Where the total coverage percentage is returned to be evaluated only.
        """
        lines_covered, lines_missed = [], []
        branches_covered, branches_missed = 0, 0

        package_name, class_name = self.extract_package_and_class_java()
        file_extension = self.get_file_extension(self.file_path)

        missed, covered = 0, 0
        if file_extension == 'xml':
            missed, covered, branches_missed, branches_covered = self.parse_missed_covered_lines_jacoco_xml(
                class_name
            )
        elif file_extension == 'csv':
            missed, covered, branches_missed, branches_covered = self.parse_missed_covered_lines_jacoco_csv(
                package_name, class_name
            )
        else:
            raise ValueError(f"Unsupported JaCoCo code coverage report format: {file_extension}")

        total_lines = missed + covered
        total_branches = branches_covered + branches_missed
        line_coverage_percentage = (float(covered) / total_lines) if total_lines > 0 else 0
        branch_coverage_percentage = (float(branches_covered) / total_branches) if total_branches > 0 else 0

        return lines_covered, lines_missed, line_coverage_percentage, branch_coverage_percentage

    def parse_missed_covered_lines_jacoco_xml(self, class_name: str) -> tuple[int, int, int, int]:
        """Parses a JaCoCo XML code coverage report to extract covered and missed line numbers for a specific file."""
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        sourcefile = root.find(f".//sourcefile[@name='{class_name}.java']")

        if sourcefile is None:
            return 0, 0, 0, 0

        missed, covered = 0, 0
        missed_branches, covered_branches = 0, 0
        for counter in sourcefile.findall('counter'):
            if counter.attrib.get('type') == 'LINE':
                missed += int(counter.attrib.get('missed', 0))
                covered += int(counter.attrib.get('covered', 0))
            elif counter.attrib.get('type') == 'BRANCH':
                missed_branches += int(counter.attrib.get('missed', 0))
                covered_branches += int(counter.attrib.get('covered', 0))

        return missed, covered, missed_branches, covered_branches

    def parse_missed_covered_lines_jacoco_csv(self, package_name: str, class_name: str) -> tuple[int, int, int, int]:
        with open(self.file_path, "r") as file:
            reader = csv.DictReader(file)
            missed, covered = 0, 0
            missed_branches, covered_branches = 0, 0
            for row in reader:
                if row["PACKAGE"] == package_name and row["CLASS"] == class_name:
                    try:
                        missed = int(row["LINE_MISSED"])
                        covered = int(row["LINE_COVERED"])
                        missed_branches = int(row["BRANCH_MISSED"])
                        covered_branches = int(row["BRANCH_COVERED"])
                        break
                    except KeyError as e:
                        self.logger.error("Missing expected column in CSV: {e}")
                        raise

        return missed, covered, missed_branches, covered_branches

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

    def get_file_extension(self, filename: str) -> str | None:
        """Get the file extension from a given filename."""
        return os.path.splitext(filename)[1].lstrip(".")