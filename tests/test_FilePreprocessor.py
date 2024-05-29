import pytest
import tempfile
import textwrap
from cover_agent.FilePreprocessor import FilePreprocessor


class TestFilePreprocessor:
    # Test for a C file
    def test_c_file(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".c") as tmp:
            preprocessor = FilePreprocessor(tmp.name)
            input_text = "Lorem ipsum dolor sit amet,\nconsectetur adipiscing elit,\nsed do eiusmod tempor incididunt."
            processed_text = preprocessor.process_file(input_text)
            assert (
                processed_text == input_text
            ), "C file processing should not alter the text."

    # Test for a Python file with only a function
    def test_py_file_with_function_only(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
            tmp.write(b"def function():\n    pass\n")
            tmp.close()
            preprocessor = FilePreprocessor(tmp.name)
            input_text = "Lorem ipsum dolor sit amet,\nconsectetur adipiscing elit,\nsed do eiusmod tempor incididunt."
            processed_text = preprocessor.process_file(input_text)
            assert (
                processed_text == input_text
            ), "Python file without class should not alter the text."

    # Test for a Python file with a comment that looks like a class definition
    def test_py_file_with_commented_class(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
            tmp.write(b"# class myPythonFile:\n#    pass\n")
            tmp.close()
            preprocessor = FilePreprocessor(tmp.name)
            input_text = "Lorem ipsum dolor sit amet,\nconsectetur adipiscing elit,\nsed do eiusmod tempor incididunt."
            processed_text = preprocessor.process_file(input_text)
            assert (
                processed_text == input_text
            ), "Commented class definition should not trigger processing."

    # Test for a Python file with an actual class definition
    def test_py_file_with_class(self):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
            tmp.write(b"class MyClass:\n    def method(self):\n        pass\n")
            tmp.close()
            preprocessor = FilePreprocessor(tmp.name)
            input_text = "Lorem ipsum dolor sit amet,\nconsectetur adipiscing elit,\nsed do eiusmod tempor incididunt."
            processed_text = preprocessor.process_file(input_text)
            expected_output = textwrap.indent(input_text, "    ")
            assert (
                processed_text == expected_output
            ), "Python file with class should indent the text."
