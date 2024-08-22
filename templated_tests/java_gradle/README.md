# Java Math Application
A simple Java application for code coverage generation testing.

## Requirements
- You must have java installed on your machine and JAVA_HOME set to your jdk.
- https://www.baeldung.com/java-macos-installation
- https://www.baeldung.com/openjdk-windows-installation
- https://www.baeldung.com/ubuntu-install-jdk
- https://www.baeldung.com/java-home-on-windows-mac-os-x-linux


## How to run
`cd` into this directory and run:
```
./gradlew clean test jacocoTestReport
```
The coverage report will be generated as `build/reports/jacoco/test/jacocoTestReport.csv`.
