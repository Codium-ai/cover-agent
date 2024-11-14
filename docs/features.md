# Cover Agent Feature Flags

## Features Overview

### 1. Diff-Based Coverage
Generates targeted tests for changes between branches, helping ensure new code is adequately tested without re-running all tests.

- **Options**:
  - `--diff-coverage`: Enables diff-based test generation.
  - `--branch=<branch_name>`: Specifies a branch for comparison (default: `main`).
- **Usage**:
  ```bash
  python cover_agent/main.py --diff-coverage --branch=develop
  ```
  This example compares the current branch with `develop`, generating tests for new changes.

- **Note**: `--diff-coverage` cannot be used with `--use-report-coverage-feature-flag`.

### 2. Report-Based Coverage
Accepts tests if they increase coverage for any file in the report, regardless of the specific source file.

- **Option**:
  - `--use-report-coverage-feature-flag`: Activates this feature to accept any coverage increase as sufficient.
- **Usage**:
  ```bash
  python cover_agent/main.py --use-report-coverage-feature-flag
  ```
  This example accepts tests that improve coverage anywhere in the report.

- **Note**: This flag is mutually exclusive with `--diff-coverage`.