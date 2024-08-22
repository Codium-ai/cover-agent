# Calculator Application
This project is a Spring Boot web application that provides a simple calculator with basic arithmetic operations.

## Prerequisites
In order to build, run, and test this service you will need:
- Java 11 or later
- [Apache Maven](https://maven.apache.org/)
- Docker (optional, if you want to use the Docker setup)

## Compile and Run
### Using Maven
To compile the project:
```bash
mvn clean install
```

To run the application:
```bash
mvn spring-boot:run
```

### Using Docker
To build and run the Docker container:
```bash
docker build -t calculator-app .
docker run -p 8080:8080 calculator-app
```

## API Endpoints
The calculator application provides the following endpoints:

- `GET /add?a=number&b=number` - Adds two numbers
- `GET /subtract?a=number&b=number` - Subtracts the second number from the first number
- `GET /multiply?a=number&b=number` - Multiplies two numbers
- `GET /divide?a=number&b=number` - Divides the first number by the second number

Example usage:
```bash
curl -X GET "http://localhost:8080/add?a=2&b=3"
```

## Testing
To run the tests:
```bash
mvn test
```

To generate a code coverage report:
```bash
mvn verify
```
This will generate a code coverage report in the `target/site/jacoco` directory.

## Project Structure
- `.gitignore` - Specifies intentionally untracked files to ignore
- `Dockerfile` - Contains the instructions to build the Docker image
- `pom.xml` - Maven Project Object Model (POM) file with project dependencies and build configuration
- `src/main/java/com/example/calculator` - Contains the main application code
  - `CalculatorApplication.java` - Entry point of the Spring Boot application
  - `controller/CalculatorController.java` - REST controller that handles the arithmetic operations
  - `service/CalculatorService.java` - Service class that contains the business logic for arithmetic operations
- `src/test/java/com/example/calculator` - Contains the test cases for the application
  - `controller/CalculatorControllerTest.java` - Test cases for the `CalculatorController`
  - `service/CalculatorServiceTest.java` - Test cases for the `CalculatorService`

## Additional Information
- The application uses Spring Boot for rapid application development.
- Maven is used for project management and build automation.
- Docker is used to containerize the application for consistent and isolated execution environments.

Feel free to contribute to this project by opening issues or submitting pull requests. For major changes, please open an issue first to discuss what you would like to change.
