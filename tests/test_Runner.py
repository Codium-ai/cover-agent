import pytest
from unittest.mock import patch
from cover_agent.Runner import Runner  # Adjust the import path as necessary


class TestRunner:
    def test_run_command_success(self):
        """Test the run_command method with a command that succeeds."""
        command = 'echo "Hello, World!"'
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        assert stdout.strip() == "Hello, World!"
        assert stderr == ""
        assert exit_code == 0

    def test_run_command_with_cwd(self):
        """Test the run_command method with a specified working directory."""
        command = 'echo "Working Directory"'
        stdout, stderr, exit_code, _ = Runner.run_command(command, cwd="/tmp")
        assert stdout.strip() == "Working Directory"
        assert stderr == ""
        assert exit_code == 0

    def test_run_command_failure(self):
        """Test the run_command method with a command that fails."""
        # Use a command that is guaranteed to fail
        command = "command_that_does_not_exist"
        stdout, stderr, exit_code, _ = Runner.run_command(command)
        assert stdout == ""
        assert (
            "command_that_does_not_exist: not found" in stderr
            or "command_that_does_not_exist: command not found" in stderr
        )
        assert exit_code != 0
