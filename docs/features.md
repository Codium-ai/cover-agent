# Features
This doc contains explanations and usages of the feature flags used in Cover Agent.

## Diff Based Coverage
This update introduces a new feature that allows for generating tests based on the differences between branches, focusing on the changes in the codebase. This is particularly useful for ensuring that new changes are adequately tested without needing to run tests on the entire codebase.

### Key Features:
- **Diff Coverage Support**: The tool can now generate tests specifically for the code changes between branches using the `diff-cover` pip package.
- **New Command-Line Options**: 
  - `--diff-coverage`: Enable this option to generate tests based on the diff between branches.
  - `--branch`: Specify the branch to compare against when using `--diff-coverage`. The default is `main`.
- **Mutually Exclusive Flags**: The `--diff-coverage` option cannot be used simultaneously with `--use-report-coverage-feature-flag`.

### How to Run:
To utilize the diff coverage feature, run the tool with the following command-line options:

```bash
python cover_agent/main.py --diff-coverage --branch=<comparison_branch>
```

Replace `<comparison_branch>` with the name of the branch you want to compare against. This will generate tests focused on the changes between your current branch and the specified comparison branch.

### Example:
```bash
python cover_agent/main.py --diff-coverage --branch=develop
```

This command will generate tests for the differences between your current branch and the `develop` branch, ensuring that new changes are adequately covered by tests.