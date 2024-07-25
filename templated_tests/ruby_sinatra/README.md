
# Sinatra Application README

## Overview
This repository contains a simple Sinatra application with several endpoints and corresponding tests. The application can perform basic arithmetic operations, check for palindromes, return the current date, calculate days until the New Year, and echo messages. The tests ensure the application's functionality, and the setup includes Docker support for easy deployment.

## Files
### `app.rb`
The main application file containing all the routes and logic for the Sinatra application.

### `test_app.rb`
Contains the test suite for the application using Minitest and Rack::Test. It tests the main routes to ensure they work as expected.

### `Gemfile`
Specifies the dependencies for the project, including Sinatra, Minitest, and testing tools like SimpleCov.

### `Dockerfile`
Defines the Docker image setup for running the Sinatra application. It uses the official Ruby image, installs dependencies, and exposes port 4567.

## Setup
### Prerequisites
- Docker
- Ruby (optional if not using Docker)
- Bundler (optional if not using Docker)

### Installation
1. **Install dependencies:**

   If using Docker, skip this step. Otherwise, run:

   ```sh
   bundle install
   ```

2. **Run the application:**

   If using Docker:

   ```sh
   docker build -t sinatra-app .
   docker run -p 4567:4567 sinatra-app
   ```

   Without Docker:

   ```sh
   ruby app.rb
   ```

### Running Tests
To run the tests, use the following command:

```sh
ruby test_app.rb
```

## Endpoints
### Root
- **GET `/`**
  - Returns a welcome message.

### Current Date
- **GET `/current-date`**
  - Returns the current date in ISO 8601 format.

### Arithmetic Operations
- **GET `/add/:num1/:num2`**
  - Adds two numbers.
- **GET `/subtract/:num1/:num2`**
  - Subtracts the second number from the first.
- **GET `/multiply/:num1/:num2`**
  - Multiplies two numbers.
- **GET `/divide/:num1/:num2`**
  - Divides the first number by the second. Returns an error if dividing by zero.
- **GET `/square/:number`**
  - Returns the square of a number.
- **GET `/sqrt/:number`**
  - Returns the square root of a number. Returns an error if the number is negative.

### Palindrome Check
- **GET `/is-palindrome/:text`**
  - Checks if the given text is a palindrome.

### Days Until New Year
- **GET `/days-until-new-year`**
  - Returns the number of days until the next New Year.

### Echo Message
- **GET `/echo/:message`**
  - Returns the given message.
