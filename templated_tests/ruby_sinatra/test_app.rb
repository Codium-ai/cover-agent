require 'simplecov'
require 'simplecov-cobertura'

SimpleCov.start do
  formatter SimpleCov::Formatter::CoberturaFormatter
  add_filter '/test/' # Optional: Exclude test directory from coverage
end

require_relative 'app'
require 'minitest/autorun'
require 'rack/test'

class MyAppTest < Minitest::Test
  include Rack::Test::Methods

  def app
    Sinatra::Application
  end

  def test_index
    get '/'
    assert last_response.ok?
    assert_equal 'application/json', last_response.content_type
    assert_equal({ message: "Welcome to the Sinatra application!" }.to_json, last_response.body)
  end

  def test_current_date
    get '/current-date'
    assert last_response.ok?
    assert_equal 'application/json', last_response.content_type
    assert_includes last_response.body, Date.today.iso8601
  end
end