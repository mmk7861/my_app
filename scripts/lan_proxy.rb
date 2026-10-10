require "socket"

listen_port = Integer(ENV.fetch("LAN_PORT", "8080"))
target_port = Integer(ENV.fetch("APP_PORT", "8000"))
server = TCPServer.new("0.0.0.0", listen_port)

puts "LAN proxy: http://0.0.0.0:#{listen_port} -> http://127.0.0.1:#{target_port}"

trap("INT") do
  server.close
  exit
end

loop do
  client = server.accept

  Thread.new(client) do |downstream|
    upstream = nil
    begin
      upstream = TCPSocket.new("127.0.0.1", target_port)
      sockets = [downstream, upstream]

      loop do
        ready = IO.select(sockets, nil, nil, 60)
        break unless ready

        connection_closed = false
        ready.first.each do |source|
          destination = source.equal?(downstream) ? upstream : downstream
          data = source.read_nonblock(16_384, exception: false)

          if data.nil?
            connection_closed = true
            break
          end

          destination.write(data) unless data == :wait_readable
        end
        break if connection_closed
      end
    rescue Errno::ECONNRESET, Errno::EPIPE, Errno::ECONNREFUSED
      # The browser or local development server closed the connection.
    ensure
      downstream.close unless downstream.closed?
      upstream&.close unless upstream&.closed?
    end
  end
end
