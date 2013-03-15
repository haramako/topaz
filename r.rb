$:.concat %w( 
lib gem/sinatra/lib gem/rack/lib gem/tilt/lib gem/rack-protection/lib 
/Users/makoto/.rbenv/versions/2.0.0-rc2/lib/ruby/2.0.0
)

require 'missing'

# s = TCPServer.new('localhost',8080)
# exit
require 'uri'


require 'webrick'


logger = WEBrick::Log.new
logger.level = WEBrick::Log::DEBUG
sv = WEBrick::HTTPServer.new( { :Port => 9999, :Logger => logger, :DocumentRoot => '.' } )
sv.start

exit


require 'rack/response'
require 'rack/commonlogger'
require 'rack/handler'
require 'rack/handler/webrick'
require 'sinatra'
exit


get '/' do
  y = Object.constants
  (y-x).join("<br/>")
end

Sinatra::Application.run!
