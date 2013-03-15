from rpython.rlib.rsocket import RSocket, INETAddress
from rpython.rlib.rpoll import select
from rpython.rlib import _rsocket_rffi

sock = RSocket()
sock.setsockopt_int( _rsocket_rffi.SOL_SOCKET, _rsocket_rffi.SO_REUSEADDR, 1 )
sock.bind( INETAddress('localhost', 9999) )
sock.listen(1)

while True:
    print sock.fd
    inl, outl, excl = select( [sock.fd], [], [] )

    for infd in inl:
        fd, addr = sock.accept()
        cli = RSocket(fd=fd)
        print cli.getpeername(), addr
        print cli
        print cli.recv(100)
