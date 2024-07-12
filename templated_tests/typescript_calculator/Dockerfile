FROM node:18

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy package.json and package-lock.json (if available) to the working directory
COPY package*.json ./

# Install any dependencies, including devDependencies for ts-node and typescript
RUN npm install

# If you're building your code for production, you might want to exclude devDependencies
# RUN npm install --only=production

# Copy the rest of your app's source code to the Docker image
COPY . .

# Your app binds to port 3000 so you'll use the EXPOSE instruction to have it mapped by the docker daemon
EXPOSE 3000

# Install ts-node and nodemon globally to run TypeScript files directly
RUN npm install -g ts-node nodemon

# Modify the CMD to use nodemon with ts-node for running TypeScript files directly
CMD [ "nodemon", "--exec", "ts-node", "./app.ts" ]