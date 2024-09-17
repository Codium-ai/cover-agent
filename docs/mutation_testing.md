# Mutation Testing in Cover Agent

## Overview of Mutation Testing

Mutation testing is a technique used to evaluate the quality and effectiveness of test suites. It involves making small changes, or "mutations," to the source code and then running the test suite to see if the tests can detect the changes. The goal is to ensure that the tests are robust enough to catch potential bugs introduced by these mutations. If a test fails due to a mutation, it indicates that the test suite is effective in catching errors. Conversely, if a mutation does not cause any test to fail, it suggests that the test suite may need improvement.

## How Mutation Testing Works in Cover Agent

In the Cover Agent, mutation testing is integrated into the `UnitTestGenerator` class. After generating and validating the tests, the mutation testing process is initiated if enabled. Here's a brief overview of how it works:

1. **Mutation Prompt Building**: The `PromptBuilder` class constructs a prompt specifically for mutation testing. This prompt guides the AI to generate potential mutations for the source code.

2. **Running Mutations**: The `run_mutations` method in the `UnitTestGenerator` class executes the mutation tests. It uses the AI to generate a list of mutations, applies each mutation to the source code, and runs the test suite to check if the mutation is detected.

3. **Logging Results**: The results of each mutation test are logged, indicating whether the mutation was caught (i.e., caused a test to fail) or survived (i.e., did not cause any test to fail).

## How to Run Mutation Testing in Cover Agent

To run mutation testing in Cover Agent, you need to use the command-line arguments added in `main.py`. Here’s how you can enable and execute mutation testing:

1. **Enable Mutation Testing**: Use the `--mutation-testing` flag when running the Cover Agent. This flag activates the mutation testing feature.

2. **Enable Detailed Logging**: If you want more detailed logging of the mutation testing process, use the `--more-mutation-logging` flag. This will provide additional information about the mutations and their effects.

### Example Command

```bash
python cover_agent/main.py <existing_arguments> --mutation-testing --more-mutation-logging
```

This command will run the Cover Agent with mutation testing enabled and provide detailed logs of the mutation process.

Note: `<existing_arguments>` denotes the regular arguments that are supplied when running Cover Agent (e.g. `--source-file-path`, `--test-file-path`, etc.). For more details see the top level `README.md` file.

## Additional Information

### Configuration

Mutation testing prompts are configured using a TOML file named `mutation_test_prompt.toml`. This file defines the strategies and templates used for generating mutations. You can customize this file to adjust the mutation strategies according to your needs.

### Limitations and Considerations

- **Performance**: Mutation testing can be resource-intensive as it involves running the test suite multiple times with different mutations.
- **Mutation Quality**: The effectiveness of mutation testing depends on the quality of the mutations generated. Ensure that the mutation strategies are well-defined to produce meaningful insights.
