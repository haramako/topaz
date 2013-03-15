module Socket
  AF_UNSPEC = nil
  SOCK_STREAM = nil
  AI_PASSIVE = nil

  def self.gethostname
    'hoge'
  end

  def self.getaddrinfo(address,port,*rest)
    [[nil,nil,nil,'0.0.0.0']]
  end

end

class TCPServer
  def fcntl(*args)
  end
end

class IO
  def eof?
    false
  end
end
