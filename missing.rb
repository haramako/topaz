
RUBY_RELEASE_DATE='2013-03-11'

class Module
  def extend_object
  end 
end

module Kernel
  def trap(signal, &block)
  end

  def rand(n=nil)
    if n
      (Random.new.rand*n).to_i
    else
      Random.new.rand
    end
  end
  def format( fmt, *args )
    fmt % args
  end
  def sprintf( fmt, *args )
    fmt % args
  end
  def caller
    begin
      raise ''
    rescue Exception => e
      return e.backtrace
    end
  end
end

class Hash
  def each_value( &block )
    values.each( &block )
  end
end


class Regexp
  EXTENDED = 1
  def self.quote(str)
    str
  end
end

class Encoding
  UTF_7 = 1
  UTF_16BE = 1
  UTF_16LE = 1
  UTF_32BE = 1
  UTF_32LE = 1
  US_ASCII = 1
end

class String
  def force_encoding( encoding )
    self
  end
  def encode!(*args)
    self
  end
  def each_line
    self.split(/\x0d?\n/).each do |line|
      yield line
    end
  end
  def each_byte
    self.size.times do |i|
      yield self.getbyte(i)
    end
  end
  def count(pat)
    i = 0
    self.gsub(/#{pat}/){ i+=1 }
    i
  end
  def sub!(*args)
    self.replace( self.sub(*args) )
  end
  def bytesize
    size
  end
  def scan(regexp)
    r = []
    self.gsub!(regexp){ |mo| r << mo[0] }
    r
  end
  def strip
    self.gsub(/\A\s+/){''}.gsub(/\a+\Z/){''}
  end
  def strip!
    self.replace self.strip
  end
  alias replace initialize_copy 
end

module Etc
end

class Mutex
  def synchronize
    yield
  end
end

module Errno
  class EADDRINUSE < RuntimeError; end
  class ENOENT < RuntimeError; end
  class EBADF < RuntimeError; end
  class EINVAL < RuntimeError; end
  class ENOTCONN < RuntimeError; end
  class EPIPE < RuntimeError; end
  class ECONNRESET < RuntimeError; end
end

class IOError < RuntimeError; end
class SocketError < RuntimeError; end

module RbConfig
  def self.ruby
    ''
  end
end

class Struct
  def self.new( *args )
    klass = Class.new
    klass.class_eval do
      args.each do |arg|
        klass.attr_accessor arg
      end
    end
    klass
  end
end

class Time
  def strftime(fmt)
    self.to_f.to_s
  end
  def utc
    self
  end
  def wday
    7
  end
  def day
    1
  end
  def mon
    1
  end
  def year
    2013
  end
  def hour
    1
  end
  def min
    1
  end
  def sec
    2
  end
end

module Fcntl
  FD_CLOEXEC = nil
  F_SETFD = nil
end

class Array
  def reverse!
    n = self.size
    (n/2).times do |i|
      self[i], self[n-i-1] = self[n-i-1], self[i]
    end
    self
  end
  def collect!(&block)
    self.replace collect(&block)
    self
  end
  def sort_by( &block )
    self.map{|x| [x, block.call(*x)] }.sort{|x| x[1] }.map{|x| x[0] }
  end
end

class IO
  def self.read(filename)
    File.open(filename,'r'){|f|f.read}
  end
  def self.select(*args)
    puts 'select'
    TCPServer.select(*args)
  end
end

class Thread
  def self.start
    yield
  end
end

class ThreadGroup
  attr_reader :list
  def initialize
    @list = []
  end
  def add(thread)
    @list << thread
  end
end

class File
  NONBLOCK = 0
  def self.mtime(file)
    Time.new
  end
end

class File::Stat
  def mtime
    Time.new
  end
end
