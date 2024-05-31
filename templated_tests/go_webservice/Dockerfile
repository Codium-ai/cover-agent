# Use the official Golang image as the base image
FROM golang:1.22

# Set the Current Working Directory inside the container
WORKDIR /app

# Copy the source code into the container
COPY . .

# Download all dependencies. Dependencies will be cached if the go.mod and go.sum files are not changed
RUN go build -buildvcs=false

# Install necessary packages for testing and coverage report generation
RUN go install github.com/stretchr/testify/assert \
    && go install github.com/axw/gocov/gocov \
    && go install github.com/AlekSi/gocov-xml

# Build the Go app
RUN go build -o /go_webservice

# Validate that the tests can be run with coverage report generation
RUN go test -coverprofile=coverage.out && gocov convert coverage.out | gocov-xml > coverage.xml