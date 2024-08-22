# Use the official Ruby image from the Docker Hub
FROM ruby:3.3

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the Gemfile into the container at /usr/src/app
COPY Gemfile ./

# Install the gems specified in the Gemfile
RUN bundle install

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Make port 4567 available to the world outside this container
EXPOSE 4567

# Define environment variable
ENV RACK_ENV=production

# Run app.rb when the container launches
CMD ["ruby", "app.rb"]