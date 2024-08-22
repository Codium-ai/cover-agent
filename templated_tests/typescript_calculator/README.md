# TypeScript Calculator Project

This project is a simple calculator implemented using TypeScript, HTML, SCSS, and Docker. The calculator supports basic arithmetic operations and is designed to run in a web browser.

## Project Structure
| File                          | Description                                                                               |
|-------------------------------|-------------------------------------------------------------------------------------------|
| **tsconfig.json**             | TypeScript configuration file specifying compiler options and compatibility settings.     |
| **Dockerfile**                | Docker configuration to containerize the application, setting up the Node.js environment. |
| **src/index.html**            | Main HTML file for the calculator interface, including necessary scripts and styles.      |
| **src/index.ts**              | Initializes the calculator and handles button interactions and display updates.           |
| **src/styles.scss**           | SCSS file for styling the calculator interface, including layout and buttons.             |
| **src/modules/Calculator.ts** | Contains the `Calculator` class with logic for arithmetic operations and state management.|
| **tests/Calculator.test.ts**  | Mocha/Chai test suite for the `Calculator` class, ensuring correct functionality.         |

## Prerequisites
- [Docker](https://www.docker.com/) installed on your system.
- [Node.js](https://nodejs.org/) and npm installed if you want to run the project locally without Docker.

## Running the Project
### Using Docker
1. **Build the Docker image**:
   ```sh
   docker build -t ts-calculator .
   ```

2. **Run the Docker container**:
   ```sh
   docker run -p 3000:3000 ts-calculator
   ```

3. **Access the application**:
   Open your web browser and go to `http://localhost:3000` to see the calculator in action.

### Running Locally
1. **Install dependencies**:
   ```sh
   npm install
   ```

2. **Compile TypeScript**:
   ```sh
   npx tsc
   ```

3. **Start the application**:
   ```sh
   npm start
   ```

4. **Access the application**:
   Open your web browser and go to `http://localhost:3000` to see the calculator in action.

## Testing
The project includes unit tests for the `Calculator` class using Mocha and Chai. To run the tests:

1. **Install dependencies**:
   ```sh
   npm install
   ```

2. **Run the tests**:
   ```sh
   npm test
   ```
