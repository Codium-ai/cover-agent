# React Calculator Application

## Overview
This is a simple calculator application built with React. The application includes exponentiation and modulus operations, and it is designed to be run within a Docker container.

## Project Structure
- `.gitignore`: Specifies files and directories to be ignored by git.
- `Dockerfile`: Defines the Docker image for the application.
- `src/index.js`: The main entry point of the React application.
- `src/setupTests.js`: Configuration for Enzyme to work with React.
- `src/tests/Calculator.test.js`: Unit tests for the Calculator component.
- `src/modules/Calculator.css`: CSS styles for the Calculator component.
- `src/modules/Calculator.js`: The main Calculator component.
- `public/index.html`: The HTML file that serves the React application.

## Prerequisites
Ensure you have Docker installed on your machine. To check if Docker is installed, run `docker --version`. It should display the Docker version if it's correctly installed.

## Building and Running the Application
### Steps to Build and Run the Application

1. **Build the Docker image:**
   Navigate to the project directory and build the Docker image by running:
   ```bash
   docker build -t react-calculator .
   ```

2. **Run the Docker container:**
   After building the image, run the container using:
   ```bash
   docker run -p 3000:3000 react-calculator
   ```
   This will start the application on `localhost:3000`.

## Testing
This section provides instructions on how to run the unit tests for the Calculator component.

### Prerequisites for Testing
- Ensure you have Node.js and npm installed on your machine.

### Running Tests
1. **Install dependencies:**
   Navigate to the project directory and install the necessary dependencies:
   ```bash
   npm install
   ```

2. **Run unit tests:**
   Execute the following command to run the unit tests:
   ```bash
   npm test
   ```

This will run the tests defined in `src/tests/Calculator.test.js`, verifying the functionality of the Calculator component.
