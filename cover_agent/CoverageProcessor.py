from cover_agent.CustomLogger import CustomLogger
from typing import Literal, Tuple, Union, List
import csv
import json
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
        diff_coverage_report_path: str = None,
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
        self.diff_coverage_report_path = diff_coverage_report_path

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
                elif self.coverage_type == "diff_cover_json":
                    return self.parse_json_diff_coverage_report()
                else:
                    raise ValueError(f"Unsupported coverage report type: {self.coverage_type}")

    def parse_coverage_report_cobertura(self, filename: str = None) -> Union[Tuple[list, list, float, float], dict]:
        """
        Parses a Cobertura XML code coverage report to extract covered and missed line numbers for a specific file
        or all files, and calculates the line and branch coverage percentages.

        Args:
            filename (str, optional): The name of the file to process. If None, processes all files.

        Returns:
            Union[Tuple[list, list, float, float], dict]: If filename is provided, returns a tuple 
            containing lists of covered and missed line numbers, the line coverage percentage, 
            and the branch coverage percentage. If filename is None, returns a dictionary with 
            filenames as keys and a tuple containing lists of covered and missed line numbers, 
            the line coverage percentage, and the branch coverage percentage as values.
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
                    lines_covered, lines_missed, coverage_percentage, branch_coverage_percentage = self.parse_coverage_data_for_class(cls)
                    coverage_data[cls_filename] = (lines_covered, lines_missed, coverage_percentage, branch_coverage_percentage)
            return coverage_data

    def parse_coverage_data_for_class(self, cls) -> Tuple[list, list, float]:
        """
        Parses coverage data for a single class.

        Args:
            cls (Element): XML element representing the class.

        Returns:
            Tuple[list, list, float, float]: A tuple containing lists of covered and missed line numbers, 
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
        Parses an LCOV coverage report file and calculates line and branch coverage.
        This method reads an LCOV coverage report file specified by `self.file_path` and 
        extracts information about covered and missed lines, as well as branch coverage.
        It calculates the percentage of line and branch coverage based on the data extracted.
        Returns:
            tuple: A tuple containing:
                - lines_covered (list): A list of line numbers that are covered.
                - lines_missed (list): A list of line numbers that are missed.
                - line_coverage_percentage (float): The percentage of lines covered.
                - branch_coverage_percentage (float): The percentage of branches covered.
        Raises:
            FileNotFoundError: If the specified file does not exist.
            IOError: If there is an error reading the file.
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

    def parse_coverage_report_jacoco(self) -> Tuple[list, list, float]:
        """
        Parses a JaCoCo XML code coverage report to extract covered and missed line numbers for a specific file,
        and calculates the line and branch coverage percentages.

        Returns:
            Tuple[list, list, float, float]: A tuple containing lists of covered and missed line numbers,
            the line coverage percentage, and the branch coverage percentage.
        """
        lines_covered, lines_missed = [], []
        branches_covered, branches_missed = 0, 0
        source_file_extension = self.get_file_extension(self.src_file_path)

        package_name, class_name = "",""
        if source_file_extension == 'java':
            package_name, class_name= self.extract_package_and_class_java()
        elif source_file_extension == 'kt':
            package_name, class_name = self.extract_package_and_class_kotlin()
        else:
            self.logger.warn(f"Unsupported Bytecode Language: {source_file_extension}. Using default Java logic.")
            package_name, class_name = self.extract_package_and_class_java()


        file_extension = self.get_file_extension(self.file_path)

        missed, covered = 0, 0
        if file_extension == 'xml':
            missed, covered, branches_missed, branches_covered  = self.parse_missed_covered_lines_jacoco_xml(
                class_name
            )
        elif file_extension == 'csv':
            missed, covered, branches_missed, branches_covered  = self.parse_missed_covered_lines_jacoco_csv(
                package_name, class_name
            )
        else:
            raise ValueError(f"Unsupported JaCoCo code coverage report format: {file_extension}")

        total_lines = missed + covered
        total_branches = branches_covered + branches_missed
        line_coverage_percentage = (float(covered) / total_lines) if total_lines > 0 else 0
        branch_coverage_percentage = (float(branches_covered) / total_branches) if total_branches > 0 else 0

        return lines_covered, lines_missed, line_coverage_percentage, branch_coverage_percentage

    def parse_missed_covered_lines_jacoco_xml(
        self, class_name: str
    ) -> tuple[int, int, int, int]:
        """
        Parses a JaCoCo XML code coverage report to extract covered and missed line numbers for a specific file,
        and calculates the line and branch coverage percentages.

        Args:
            class_name (str): The name of the class to process.

        Returns:
            tuple: A tuple containing:
            - missed (int): The number of missed lines.
            - covered (int): The number of covered lines.
            - missed_branches (int): The number of missed branches.
            - covered_branches (int): The number of covered branches.
        """
        tree = ET.parse(self.file_path)
        root = tree.getroot()
        sourcefile = (
                root.find(f".//sourcefile[@name='{class_name}.java']") or
                root.find(f".//sourcefile[@name='{class_name}.kt']")
        )

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

    def parse_missed_covered_lines_jacoco_csv(
        self, package_name: str, class_name: str
    ) -> tuple[int, int, int, int]:
        """
        Parses the JaCoCo CSV report to extract the number of missed and covered lines and branches for a specific class.
        Args:
            package_name (str): The name of the package to filter the CSV data.
            class_name (str): The name of the class to filter the CSV data.
        Returns:
            tuple[int, int, int, int]: A tuple containing the number of missed lines, covered lines, missed branches, and covered branches.
        Raises:
            KeyError: If the expected columns are not found in the CSV file.
        """
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
                        self.logger.error(f"Missing expected column in CSV: {str(e)}")
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
    def extract_package_and_class_kotlin(self):
        package_pattern = re.compile(r"^\s*package\s+([\w.]+)\s*(?:;)?\s*(?://.*)?$")
        class_pattern = re.compile(r"^\s*(?:public|internal|abstract|data|sealed|enum|open|final|private|protected)*\s*class\s+(\w+).*")

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

    def parse_json_diff_coverage_report(self) -> Tuple[List[int], List[int], float]:
        """
        Parses a JSON-formatted diff coverage report to extract covered lines, missed lines,
        and the coverage percentage for the specified src_file_path.
        Returns:
            Tuple[List[int], List[int], float]: A tuple containing lists of covered and missed lines,
                                                and the coverage percentage.
        """
        with open(self.diff_coverage_report_path, "r") as file:
            report_data = json.load(file)

        # Create relative path components of `src_file_path` for matching
        src_relative_path = os.path.relpath(self.src_file_path)
        src_relative_components = src_relative_path.split(os.sep)

        # Initialize variables for covered and missed lines
        relevant_stats = None

        for file_path, stats in report_data["src_stats"].items():
            # Split the JSON's file path into components
            file_path_components = file_path.split(os.sep)

            # Match if the JSON path ends with the same components as `src_file_path`
            if (
                file_path_components[-len(src_relative_components) :]
                == src_relative_components
            ):
                relevant_stats = stats
                break

        # If a match is found, extract the data
        if relevant_stats:
            covered_lines = relevant_stats["covered_lines"]
            violation_lines = relevant_stats["violation_lines"]
            coverage_percentage = (
                relevant_stats["percent_covered"] / 100
            )  # Convert to decimal
        else:
            # Default values if the file isn't found in the report
            covered_lines = []
            violation_lines = []
            coverage_percentage = 0.0

        return covered_lines, violation_lines, coverage_percentage


    def get_file_extension(self, filename: str) -> str | None:
        """Get the file extension from a given filename."""
        return os.path.splitext(filename)[1].lstrip(".")
