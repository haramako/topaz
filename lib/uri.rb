# URI is a module providing classes to handle Uniform Resource Identifiers
# (RFC2396[http://tools.ietf.org/html/rfc2396])
#
# == Features
#
# * Uniform handling of handling URIs
# * Flexibility to introduce custom URI schemes
# * Flexibility to have an alternate URI::Parser (or just different patterns
#   and regexp's)
#
# == Basic example
#
#   require 'uri'
#
#   uri = URI("http://foo.com/posts?id=30&limit=5#time=1305298413")
#   #=> #<URI::HTTP:0x00000000b14880
#         URL:http://foo.com/posts?id=30&limit=5#time=1305298413>
#   uri.scheme
#   #=> "http"
#   uri.host
#   #=> "foo.com"
#   uri.path
#   #=> "/posts"
#   uri.query
#   #=> "id=30&limit=5"
#   uri.fragment
#   #=> "time=1305298413"
#
#   uri.to_s
#   #=> "http://foo.com/posts?id=30&limit=5#time=1305298413"
#
# == Adding custom URIs
#
#   module URI
#     class RSYNC < Generic
#       DEFAULT_PORT = 873
#     end
#     @@schemes['RSYNC'] = RSYNC
#   end
#   #=> URI::RSYNC
#
#   URI.scheme_list
#   #=> {"FTP"=>URI::FTP, "HTTP"=>URI::HTTP, "HTTPS"=>URI::HTTPS,
#        "LDAP"=>URI::LDAP, "LDAPS"=>URI::LDAPS, "MAILTO"=>URI::MailTo,
#        "RSYNC"=>URI::RSYNC}
#
#   uri = URI("rsync://rsync.foo.com")
#   #=> #<URI::RSYNC:0x00000000f648c8 URL:rsync://rsync.foo.com>
#
# == RFC References
#
# A good place to view an RFC spec is http://www.ietf.org/rfc.html
#
# Here is a list of all related RFC's.
# - RFC822[http://tools.ietf.org/html/rfc822]
# - RFC1738[http://tools.ietf.org/html/rfc1738]
# - RFC2255[http://tools.ietf.org/html/rfc2255]
# - RFC2368[http://tools.ietf.org/html/rfc2368]
# - RFC2373[http://tools.ietf.org/html/rfc2373]
# - RFC2396[http://tools.ietf.org/html/rfc2396]
# - RFC2732[http://tools.ietf.org/html/rfc2732]
# - RFC3986[http://tools.ietf.org/html/rfc3986]
#
# == Class tree
#
# - URI::Generic (in uri/generic.rb)
#   - URI::FTP - (in uri/ftp.rb)
#   - URI::HTTP - (in uri/http.rb)
#     - URI::HTTPS - (in uri/https.rb)
#   - URI::LDAP - (in uri/ldap.rb)
#     - URI::LDAPS - (in uri/ldaps.rb)
#   - URI::MailTo - (in uri/mailto.rb)
# - URI::Parser - (in uri/common.rb)
# - URI::REGEXP - (in uri/common.rb)
#   - URI::REGEXP::PATTERN - (in uri/common.rb)
# - URI::Util - (in uri/common.rb)
# - URI::Escape - (in uri/common.rb)
# - URI::Error - (in uri/common.rb)
#   - URI::InvalidURIError - (in uri/common.rb)
#   - URI::InvalidComponentError - (in uri/common.rb)
#   - URI::BadURIError - (in uri/common.rb)
#
# == Copyright Info
#
# Author:: Akira Yamada <akira@ruby-lang.org>
# Documentation::
#   Akira Yamada <akira@ruby-lang.org>
#   Dmitry V. Sabanin <sdmitry@lrn.ru>
#   Vincent Batts <vbatts@hashbangbash.com>
# License::
#  Copyright (c) 2001 akira yamada <akira@ruby-lang.org>
#  You can redistribute it and/or modify it under the same term as Ruby.
# Revision:: $Id: uri.rb 31555 2011-05-13 20:03:21Z drbrain $
#

module URI
  # :stopdoc:
  VERSION_CODE = '000911'.freeze
  # VERSION = VERSION_CODE.scan(/../).collect{|n| n.to_i}.join('.').freeze # haramako deleted
  VERSION = '0.9.11'
  # :startdoc:

  module REGEXP

    module PATTERN
      # :stopdoc:

      # RFC 2396 (URI Generic Syntax)
      # RFC 2732 (IPv6 Literal Addresses in URL's)
      # RFC 2373 (IPv6 Addressing Architecture)

      # alpha         = lowalpha | upalpha
      ALPHA = "a-zA-Z"
      # alphanum      = alpha | digit
      ALNUM = "#{ALPHA}\\d"

      # hex           = digit | "A" | "B" | "C" | "D" | "E" | "F" |
      #                         "a" | "b" | "c" | "d" | "e" | "f"
      HEX     = "a-fA-F\\d"
      # escaped       = "%" hex hex
      ESCAPED = "%[#{HEX}]{2}"
      # mark          = "-" | "_" | "." | "!" | "~" | "*" | "'" |
      #                 "(" | ")"
      # unreserved    = alphanum | mark
      UNRESERVED = "\\-_.!~*'()#{ALNUM}"
      # reserved      = ";" | "/" | "?" | ":" | "@" | "&" | "=" | "+" |
      #                 "$" | ","
      # reserved      = ";" | "/" | "?" | ":" | "@" | "&" | "=" | "+" |
      #                 "$" | "," | "[" | "]" (RFC 2732)
      RESERVED = ";/?:@&=+$,\\[\\]"

      # domainlabel   = alphanum | alphanum *( alphanum | "-" ) alphanum
      DOMLABEL = "(?:[#{ALNUM}](?:[-#{ALNUM}]*[#{ALNUM}])?)"
      # toplabel      = alpha | alpha *( alphanum | "-" ) alphanum
      TOPLABEL = "(?:[#{ALPHA}](?:[-#{ALNUM}]*[#{ALNUM}])?)"
      # hostname      = *( domainlabel "." ) toplabel [ "." ]
      HOSTNAME = "(?:#{DOMLABEL}\\.)*#{TOPLABEL}\\.?"

      # :startdoc:
    end # PATTERN

    # :startdoc:
  end # REGEXP

  class Data
    attr_accessor :schema, :host, :port, :path, :query
    def to_s
      "#{schema} :// #{host} / #{path} ? #{query}"
    end
    def absolute?
      path and path[0] == '/'
    end
  end
  
  def self.parse(uri)
    # mo = uri.match( %r{^((\S+)://)?([^?]*)(\?.*)} )
    mo = uri.match( %r{^((\S+)://)?([a-zA-Z0-9_\-/.]*)(\?.*)?} )
    raise InvalidURIError unless mo
    r = Data.new
    r.schema = mo[2]
    r.path = mo[3]
    r.query = mo[4]
    r
  end

end

