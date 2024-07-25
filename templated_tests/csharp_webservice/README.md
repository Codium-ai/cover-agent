# Calculator Program
This project is an ASP.NET Core Web API that provides a simple calculator with basic arithmetic operations.

## Prerequisites
In order to build, run and test this service you will need the [.Net 8 SDK](https://dotnet.microsoft.com/en-us/download/dotnet/8.0)

## Compile and Run
Compile the calculator:

```bash
dotnet build dotnet build CalculatorApi
```

Run the calculator:

```bash
dotnet run --project CalculatorApi/CalculatorApi.csproj
```

Use the Api:

```bash
curl -X 'GET' 'http://127.0.0.1:5085/Calculator/add?a=1&b=2'
```

## Testing
Run the tests with code coverage:

```bash
dotnet test --collect:'XPlat Code Coverage' CalculatorApi.Tests/
```
This will output a coverage report at `CalculatorApi.Tests/TestResults/**/coverage.cobertura.xml`