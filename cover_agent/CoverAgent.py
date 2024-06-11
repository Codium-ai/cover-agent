import datetime
import os
import shutil
import sys
import wandb

from cover_agent.CustomLogger import CustomLogger
from cover_agent.ReportGenerator import ReportGenerator
from cover_agent.UnitTestGenerator import UnitTestGenerator
from cover_agent.utils import load_yaml


class CoverAgent:
    def __init__(self, args):
        self.args = args
        self.logger = CustomLogger.get_logger(__name__)

        self._validate_paths()
        self._duplicate_test_file()

        self.test_gen = UnitTestGenerator(
            source_file_path=args.source_file_path,
            test_file_path=args.test_file_output_path,
            code_coverage_report_path=args.code_coverage_report_path,
            test_command=args.test_command,
            test_command_dir=args.test_command_dir,
            included_files=args.included_files,
            coverage_type=args.coverage_type,
            desired_coverage=args.desired_coverage,
            additional_instructions=args.additional_instructions,
            llm_model=args.model,
            api_base=args.api_base,
        )

    def _validate_paths(self):
        if not os.path.isfile(self.args.source_file_path):
            raise FileNotFoundError(
                f"Source file not found at {self.args.source_file_path}"
            )
        if not os.path.isfile(self.args.test_file_path):
            raise FileNotFoundError(
                f"Test file not found at {self.args.test_file_path}"
            )

    def _duplicate_test_file(self):
        if self.args.test_file_output_path != "":
            shutil.copy(self.args.test_file_path,
                        self.args.test_file_output_path)
        else:
            self.args.test_file_output_path = self.args.test_file_path

    def generate_response(self):
        with open(self.args.code_coverage_report_path, "r") as f:
            code_cov_file = str(f.read())

        file_name = self.test_gen.source_file_path.split('/')[-1]

        prompt = f"""
                ## Overview
                
                Hi Mr. Llama, here is the jacoco code coverage report for the test suite.
                =========
                {code_cov_file}
                =========
                
                I'll start you off with an example. In that file, you'll find lots of blocks that look like this: 
                
                Here are some instructions: 
                1. The coverage we particularly care about is only for the `{file_name}.kt`. To find the information of this file, 
                you'll find it underneath the <sourcefile name="{file_name}"> block.
                2. In the `<sourcefile name="{file_name}">` block, you will find information about the instructions on each line hit, 
                as well as the methods, lines, and classes' coverages. 
                3. We only want you to consider the line by line coverage of this file. That information can be found in the 
                <counter type="LINE" missed="3" covered="3"/> line. 
                
                So for example, if we say that we care about the line coverage for `{file_name}`, you should look for a block that 
                looks like this in the coverage report: 
                
                <sourcefile name="{file_name}">
                    <line nr="5" mi="5" ci="0" mb="2" cb="0"/>
                    <line nr="6" mi="4" ci="0" mb="0" cb="0"/>
                    <line nr="8" mi="1" ci="0" mb="0" cb="0"/>
                    <line nr="13" mi="0" ci="5" mb="0" cb="2"/>
                    <line nr="14" mi="0" ci="4" mb="0" cb="0"/>
                    <line nr="16" mi="0" ci="1" mb="0" cb="0"/>
                    <counter type="INSTRUCTION" missed="10" covered="10"/>
                    <counter type="BRANCH" missed="2" covered="2"/>
                    <counter type="LINE" missed="3" covered="3"/>
                    <counter type="COMPLEXITY" missed="2" covered="2"/>
                    <counter type="METHOD" missed="1" covered="1"/>
                    <counter type="CLASS" missed="0" covered="1"/>
                </sourcefile>
                
                In this case, the `LINE` XML tag says that there are 3 missed and 3 covered lines. That means there were 6 lines 
                in total in the `{file_name}` file, and 3 were missed and 3 were covered by tests. The coverage percentage 
                in this case would be 50%. If our target percentage was 75%, this wouldn't be acceptable.

                Now, please tell us the following information: 1) the number of lines covered, 2) the total 
                number of lines in the file, as well as 3) the percentage of lines covered. 
                
                And please do so in the following output: 
                
                Example output:
                ```yaml
                lines_covered: ...
                total_lines: ...
                ```
                
                The Response should be only a valid YAML object, without any introduction text or follow-up text.
                DO NOT ADD ANYTHING AFTER YOUR ANSWER. I DON'T WANT YOU TO SAY ANYTHING EXCEPT THE TWO YAML FIELDS AND THEIR INTEGER VALUES
                
                Answer:
                ```yaml
                """
        print("Prompt", prompt)
        response = ""
        attempts = 0
        while "```yaml" not in response:
            attempts += 1
            print('attempts', attempts)
            response, prompt_token_count, response_token_count = (
                self.test_gen.ai_caller.call_model(prompt={
                    "system": "",
                    "user": prompt
                })
            )

        return response

    def run(self):
        if 'WANDB_API_KEY' in os.environ:
            wandb.login(key=os.environ['WANDB_API_KEY'])
            time_and_date = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            run_name = f"{self.args.model}_" + time_and_date
            wandb.init(project="cover-agent", name=run_name)

        iteration_count = 0
        test_results_list = []

        self.test_gen.initial_test_suite_analysis()

        while (
            self.test_gen.current_coverage < (
                self.test_gen.desired_coverage / 100)
            and iteration_count < self.args.max_iterations
        ):
            self.logger.info(
                f"Current Coverage: {round(self.test_gen.current_coverage * 100, 2)}%"
            )
            self.logger.info(
                f"Desired Coverage: {self.test_gen.desired_coverage}%")

            generated_tests_dict = self.test_gen.generate_tests(
                max_tokens=4096)

            for generated_test in generated_tests_dict.get("new_tests", []):
                test_result = self.test_gen.validate_test(
                    generated_test, generated_tests_dict
                )
                test_results_list.append(test_result)

            iteration_count += 1

            if self.test_gen.current_coverage < (
                self.test_gen.desired_coverage / 100
            ):
                prompt = self.test_gen.prompt_builder.build_prompt_custom(
                    file="analyze_test_coverage"
                )

                response = self.generate_response()

                #
                # Example output:
                # ```yaml
                # lines_covered: ...
                # total_lines: ...
                # ```

                resp = load_yaml(response, keys_fix_yaml=[
                                 "lines_covered", "total_lines"])
                print("response yaml", resp)
                total_lines = resp["total_lines"]
                lines_covered = resp["lines_covered"]
                print("lines_covered", lines_covered)
                print("total_lines", total_lines)
                self.test_gen.current_coverage = int(
                    lines_covered) / int(total_lines)

                print("prompt", prompt)
                print("response", response)

                # self.test_gen.run_coverage()

        if self.test_gen.current_coverage >= (self.test_gen.desired_coverage / 100):
            self.logger.info(
                f"Reached above target coverage of {self.test_gen.desired_coverage}% (Current Coverage: {round(self.test_gen.current_coverage * 100, 2)}%) in {iteration_count} iterations."
            )
        elif iteration_count == self.args.max_iterations:
            failure_message = f"Reached maximum iteration limit without achieving desired coverage. Current Coverage: {round(self.test_gen.current_coverage * 100, 2)}%"
            if self.args.strict_coverage:
                # User requested strict coverage (similar to "--cov-fail-under in pytest-cov"). Fail with exist code 2.
                self.logger.error(failure_message)
                sys.exit(2)
            else:
                self.logger.info(failure_message)

        ReportGenerator.generate_report(
            test_results_list, self.args.report_filepath
        )

        if 'WANDB_API_KEY' in os.environ:
            wandb.finish()
