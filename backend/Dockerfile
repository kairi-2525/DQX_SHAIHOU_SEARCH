FROM ruby:3.2.5
RUN apt-get update -qq && apt-get install -y libpq-dev
RUN mkdir /app
WORKDIR /app
ADD Gemfile /app/Gemfile
ADD Gemfile.lock /app/Gemfile.lock
RUN bundle install
ADD . /app