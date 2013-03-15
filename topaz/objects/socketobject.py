from rpython.rlib.rsocket import RSocket, INETAddress
from rpython.rlib import _rsocket_rffi
from rpython.rlib.rpoll import select, SelectError

from topaz.module import Module, ModuleDef, ClassDef
from topaz.objects.objectobject import W_Object
from topaz.objects.ioobject import W_IOObject

class W_SocketObject(Module):
    moduledef = ModuleDef("Socket", filepath=__file__)

    @moduledef.setup_module
    def setup_module(space, w_mod):
        space.set_const(w_mod, "Option", W_SocketOption.new)

class W_SocketOption(W_Object):
    classdef = ClassDef("Option", W_Object.classdef, filepath=__file__)

    
class W_BasicSocketObject(W_IOObject):
    classdef = ClassDef("BasicSocket", W_IOObject.classdef, filepath=__file__)
    fd_sock = {}

    def __init__(self, space):
        W_IOObject.__init__(self, space)
        self._sync = False

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        cls._global_do_not_reverse_lookup = False

    @classdef.singleton_method("do_not_reverse_lookup")
    def singleton_method_do_not_reverse_lookup(self, space):
        return space.newbool(W_BasicSocketObject._global_do_not_reverse_lookup)

    @classdef.singleton_method("do_not_reverse_lookup=", val="bool")
    def singleton_method_do_not_reverse_lookup_set(self, space, val):
        W_BasicSocketObject._global_do_not_reverse_lookup = val
        return space.newbool(val)

    @classmethod
    def for_fd(self, space, fd):
        if fd in self.fd_sock:
            return self.fd_sock[fd]
        else:
            return None
        
    @classdef.singleton_method("for_fd")
    def method_for_fd(self, space):
        raise NotImplementedError()

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_BasicSocketObject(space)
        
    @classdef.method("initialize")
    def method_initialize(self, space):
        self._do_not_reverse_lookup = self._global_do_not_reverse_lookup
        
    @classdef.method("connect_address")
    def method_connect_address(self, space):
        raise NotImplementedError()
        
    @classdef.method("do_not_reverse_lookup")
    def method_do_not_reverse_lookup(self, space):
        return space.newbool(self._do_not_reverse_lookup)

    @classdef.method("do_not_reverse_lookup=", val="bool")
    def method_do_not_reverse_lookup_set(self, space, val):
        self._do_not_reverse_lookup = val
        return space.newbool(val)
    
    @classdef.method("sync")
    def method_sync(self, space):
        return space.newbool(self._sync)
    
    @classdef.method("sync=", val="bool")
    def method_sync_set(self, space, val):
        self._sync = val
        return space.newbool(val)
    

class W_IPSocketObject(W_BasicSocketObject):
    classdef = ClassDef("IPSocket", W_BasicSocketObject.classdef, filepath=__file__)

    def __init__(self, space, sock=None):
        W_BasicSocketObject.__init__(self, space)
        if sock:
            self.sock = sock
            self.fd = sock.fd

    @classdef.method("peeraddr")
    def method_peeraddr(self, space):
        addr = self.sock.getpeername()
        return space.newarray([
                space.newstr_fromstr("AF_INET"),
                space.newint(addr.get_port()),
                space.newstr_fromstr(addr.get_host()),
                space.newstr_fromstr(addr.get_host())])
            
class W_TCPSocketObject(W_IPSocketObject):
    classdef = ClassDef("TCPSocket", W_IPSocketObject.classdef, filepath=__file__)

    def __init__(self, space, sock=None):
        W_IPSocketObject.__init__(self, space, sock)

            
class W_TCPServerObject(W_BasicSocketObject):
    classdef = ClassDef("TCPServer", W_BasicSocketObject.classdef, filepath=__file__)

    def __init__(self, space):
        W_BasicSocketObject.__init__(self, space)
        
    @classdef.setup_class
    def setup_class(cls,space,w_cls):
        pass

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_TCPServerObject(space)
    
    @classdef.method("initialize")
    def method_initialize(self, space, w_host, w_service):
        host = space.str0_w(w_host)
        service = space.int_w(w_service)
        addr = INETAddress(host, service)
        self.sock = RSocket()
        self.sock.setsockopt_int( _rsocket_rffi.SOL_SOCKET, _rsocket_rffi.SO_REUSEADDR, 1 )
        self.sock.bind(addr)
        self.sock.listen(5)
        self.fd = self.sock.fd
        W_BasicSocketObject.fd_sock[self.fd] = self
        return self

    @classdef.method("listen", backlog="int")
    def method_listen(self, space, backlog=5):
        self.sock.listen(backlog)
        return space.newint(0)

    @classdef.method("accept")
    def method_accept(self, space):
        fd, addr = self.sock.accept()
        sock = RSocket(fd=fd)
        w_sock = W_TCPSocketObject(space,sock)
        return w_sock

    @classdef.singleton_method("select", timeout="float")
    def method_select(self, space, w_inl, w_outl, w_excl, timeout):
        if w_inl is not space.w_nil:
            inl = [io.fd for io in w_inl.listview(space)]
        else:
            inl = []
        if w_outl is not space.w_nil:
            outl = [io.fd for io in w_outl.listview(space)]
        else:
            outl = []
        if w_excl is not space.w_nil:
            excl = [io.fd for io in w_excl.listview(space)]
        else:
            excl = []
        # print inl, outl, excl, timeout
        try:
            inl, outl, excl = select(inl, outl, excl, timeout)
        except SelectError as e:
            print e.get_msg()
            return space.w_nil
        # print inl, outl, excl
        w_inl = space.newarray([W_BasicSocketObject.for_fd(space, fd) for fd in inl])
        w_outl = space.newarray([W_BasicSocketObject.for_fd(space, fd) for fd in outl])
        w_excl = space.newarray([W_BasicSocketObject.for_fd(space, fd) for fd in excl])
        return space.newarray([w_inl, w_outl, w_excl])
