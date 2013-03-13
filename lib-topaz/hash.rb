class Hash
  def each
    iter = Topaz::HashIterator.new(self)
    while true
      begin
        key, value = iter.next()
      rescue StopIteration
        return
      end
      yield key, value
    end
  end
  alias each_pair each

  def each_key
    each { |k, v| yield k }
  end

  def ==(other)
    if self.equal?(other)
      return true
    end
    if !other.kind_of?(Hash)
      return false
    end
    if self.size != other.size
      return false
    end
    self.each do |key, value|
      if !other.has_key?(key) || other[key] != value
        return false
      end
    end
    return true
  end

  def merge!(other, &block)
    other = other.to_hash unless other.kind_of? Hash
    if block
      other.each do |key, val|
        if has_key? key
          self[key] = block.call key, self[key], val
        else
          self[key] = val
        end
      end
    else
      other.each do |key, val|
        self[key] = val
      end
    end
    self
  end

  def merge(other, &block)
    dup.merge! other, &block
  end

  def assoc(key)
    each do |k, v|
      return [k, v] if key == k
    end
    nil
  end

  def rassoc(value)
    each do |k, v|
      return [k, v] if value == v
    end
    nil
  end

  def self.[](*args)
    if args.size == 1
      obj = args.first

      if hash = Topaz::Type.convert_type(obj, Hash, :to_hash, false)
        return allocate.replace(hash)
      elsif array = Topaz::Type.convert_type(obj, Array, :to_ary, false)
        h = new
        array.each do |arr|
          next unless arr.respond_to?(:to_ary)
          arr = arr.to_ary
          next unless (1..2).include?(arr.size)
          h[arr.at(0)] = arr.at(1)
        end
        return h
      end
    end

    return new if args.empty?

    if args.size.odd?
      raise ArgumentError, "Expected an even number, got #{args.length}"
    end

    hash = new
    i = 0
    total = args.size

    while i < total
      hash[args[i]] = args[i+1]
      i += 2
    end

    hash
  end

  def update(other_hash)
    other_hash.each do |k,v|
      self[k] = v
    end
    self
  end
end
