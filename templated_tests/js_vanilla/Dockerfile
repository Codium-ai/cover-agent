FROM node:18

WORKDIR /app

# Install glibc
RUN apt-get update && \
    apt-get install -y libc6

COPY . ./

RUN npm install
RUN npm run test:coverage
