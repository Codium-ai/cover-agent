require 'sinatra'
require 'date'
require 'json'

set :bind, '0.0.0.0'

get '/' do
  content_type :json
  { message: "Welcome to the Sinatra application!" }.to_json
end

get '/current-date' do
  content_type :json
  { date: Date.today.iso8601 }.to_json
end

get '/add/:num1/:num2' do
  result = params['num1'].to_i + params['num2'].to_i
  content_type :json
  { result: result }.to_json
end

get '/subtract/:num1/:num2' do
  result = params['num1'].to_i - params['num2'].to_i
  content_type :json
  { result: result }.to_json
end

get '/multiply/:num1/:num2' do
  result = params['num1'].to_i * params['num2'].to_i
  content_type :json
  { result: result }.to_json
end

get '/divide/:num1/:num2' do
  num2 = params['num2'].to_i
  halt 400, { error: "Cannot divide by zero" }.to_json if num2 == 0
  result = params['num1'].to_i / num2.to_f
  content_type :json
  { result: result }.to_json
end

get '/square/:number' do
  number = params['number'].to_i
  content_type :json
  { result: number**2 }.to_json
end

get '/sqrt/:number' do
  number = params['number'].to_f
  halt 400, { error: "Cannot take square root of a negative number" }.to_json if number < 0
  content_type :json
  { result: Math.sqrt(number) }.to_json
end

get '/is-palindrome/:text' do
  text = params['text']
  content_type :json
  { is_palindrome: text == text.reverse }.to_json
end

get '/days-until-new-year' do
  today = Date.today
  next_new_year = Date.new(today.year + 1, 1, 1)
  delta = (next_new_year - today).to_i
  content_type :json
  { days_until_new_year: delta }.to_json
end

get '/echo/:message' do
  message = params['message']
  content_type :json
  { message: message }.to_json
end