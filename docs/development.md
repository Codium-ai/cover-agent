## Development
This section discusses the development of this project.

### Versioning
Before merging to main make sure to manually increment the version number in `cover_agent/version.txt` at the root of the repository.

### Running Tests
Set up your development environment by running the `poetry install` command as you did above. 

Note: for older versions of Poetry you may need to include the `--dev` option to install Dev dependencies.

After setting up your environment run the following command:
```shell
poetry run pytest --junitxml=testLog.xml --cov=templated_tests --cov=cover_agent --cov-report=xml --cov-report=term --log-cli-level=INFO
```
This will also generate all logs and output reports that are generated in `.github/workflows/ci_pipeline.yml`.

### Running the app locally from source

#### Prerequisites
- Python3
- Poetry

#### Steps
1. If not already done, install the dependencies
    ```shell
    poetry install
    ```

2. Let Poetry manage / create the environment
    ```shell
   poetry shell
   ```

3. Run the app
    ```shell
   poetry run cover-agent \
     --source-file-path <path_to_source_file> \
     [other_options...]
    ```

Notice that you're prepending `poetry run` to your `cover-agent` command. Replace `<path_to_your_source_file>` with the
actual path to your source file. Add any other necessary options as described in
the [Running the Code](#running-the-code) section.

### Building the binary locally
You can build the binary locally simply by invoking the `make installer` command. This will run PyInstaller locally on your machine. Ensure that you have set up the poetry project first (i.e. running `poetry install`).
