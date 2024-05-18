import subprocess
import time


class Runner:
    @staticmethod
    def run_command(command, cwd=None):
        """
        Executes a shell command in a specified working directory and returns its output, error, and exit code.

        Parameters:
            command (str): The shell command to execute.
            cwd (str, optional): The working directory in which to execute the command. Defaults to None.

        Returns:
            tuple: A tuple containing the standard output ('stdout'), standard error ('stderr'), exit code ('exit_code'), and the time of the executed command ('command_start_time').
        """
        # Get the current time before running the test command, in milliseconds
        command_start_time = int(round(time.time() * 1000))

        # Ensure the command is executed with shell=True for string commands
        result = subprocess.run(
            command, shell=True, cwd=cwd, text=True, capture_output=True
        )

        # Return a dictionary with the desired information
        return result.stdout, result.stderr, result.returncode, command_start_time
