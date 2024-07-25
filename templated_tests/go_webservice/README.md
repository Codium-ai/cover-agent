
# Go Gin Web Application

## Building and Running the Application
This guide describes how to build and run the Go web application using the Gin framework.

### Prerequisites
Ensure you have Go installed on your machine. To check if Go is installed, run `go version`. It should display the Go version if it's correctly installed.

### Steps to Run the Application
1. **Build the application:**
   Build the application by running:
   ```bash
   go build
   ```

2. **Run the application:**
   After building the application, run it using:
   ```bash
   ./go_webservice
   ```
   This will start the server on `localhost:8080`.

## Testing
This section provides instructions on how to run tests and generate a Cobertura coverage report for the application.

### Prerequisites for Testing
- Install the required Go packages for testing and coverage report generation:
  ```bash
  go install github.com/stretchr/testify/assert
  go install github.com/axw/gocov/gocov
  go install github.com/AlekSi/gocov-xml
  ```

### Running Tests
1. **Run unit tests:**
   Execute the following command to run the unit tests:
   ```bash
   go test -v
   ```

2. **Check code coverage:**
   Run tests with the coverage flag to check code coverage:
   ```bash
   go test -v -cover
   ```

### Generating Cobertura Coverage Report
1. **Generate coverage data:**
   First, generate the test coverage data:
   ```bash
   go test -coverprofile=coverage.out
   ```

2. **Convert coverage data to Cobertura format:**
   Use `gocov` and `gocov-xml` to convert the coverage data to Cobertura XML format:
   ```bash
   export PATH="$HOME/go/bin:$PATH"
   gocov convert coverage.out | gocov-xml > coverage.xml
   ```

   You can now use `coverage.xml` with tools that support Cobertura formatted coverage reports.
