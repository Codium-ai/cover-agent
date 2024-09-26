import pytest
from cover_agent.UnitTestGenerator import UnitTestGenerator
from cover_agent.ReportGenerator import ReportGenerator
import os

from unittest.mock import patch, mock_open


class TestUnitTestGenerator:
    def test_get_included_files_mixed_paths(self):
        with patch("builtins.open", mock_open(read_data="file content")) as mock_file:
            mock_file.side_effect = [
                IOError("File not found"),
                mock_open(read_data="file content").return_value,
            ]
            included_files = ["invalid_file1.txt", "valid_file2.txt"]
            result = UnitTestGenerator.get_included_files(included_files)
            assert (
                result
                == "file_path: `valid_file2.txt`\ncontent:\n```\nfile content\n```"
            )

    def test_get_included_files_valid_paths(self):
        with patch("builtins.open", mock_open(read_data="file content")):
            included_files = ["file1.txt", "file2.txt"]
            result = UnitTestGenerator.get_included_files(included_files)
            assert (
                result
                == "file_path: `file1.txt`\ncontent:\n```\nfile content\n```\nfile_path: `file2.txt`\ncontent:\n```\nfile content\n```"
            )
