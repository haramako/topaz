import os
import sys
import stat

from topaz.coerce import Coerce
from topaz.error import error_for_oserror
from topaz.module import ClassDef
from topaz.objects.arrayobject import W_ArrayObject
from topaz.objects.hashobject import W_HashObject
from topaz.objects.objectobject import W_Object
from topaz.objects.ioobject import W_IOObject
from topaz.objects.stringobject import W_StringObject
from topaz.system import IS_WINDOWS
from topaz.utils.ll_file import O_BINARY, ftruncate, isdir, fchmod
from topaz.utils.filemode import map_filemode


FNM_NOESCAPE = 0x01
FNM_PATHNAME = 0x02
FNM_DOTMATCH = 0x04


class W_FileObject(W_IOObject):
    classdef = ClassDef("File", W_IOObject.classdef, filepath=__file__)

    @classdef.setup_class
    def setup_class(cls, space, w_cls):
        if IS_WINDOWS:
            w_alt_seperator = space.newstr_fromstr("\\")
            w_fnm_syscase = space.newint(0x08)
        else:
            w_alt_seperator = space.w_nil
            w_fnm_syscase = space.newint(0)
        space.set_const(w_cls, "SEPARATOR", space.newstr_fromstr("/"))
        space.set_const(w_cls, "ALT_SEPARATOR", w_alt_seperator)
        space.set_const(w_cls, "PATH_SEPARATOR", space.newstr_fromstr(os.pathsep))
        space.set_const(w_cls, "FNM_SYSCASE", w_fnm_syscase)
        space.set_const(w_cls, "FNM_NOESCAPE", space.newint(FNM_NOESCAPE))
        space.set_const(w_cls, "FNM_PATHNAME", space.newint(FNM_PATHNAME))
        space.set_const(w_cls, "FNM_DOTMATCH", space.newint(FNM_DOTMATCH))
        space.set_const(w_cls, "BINARY", space.newint(O_BINARY))
        space.set_const(w_cls, "RDONLY", space.newint(os.O_RDONLY))
        space.set_const(w_cls, "WRONLY", space.newint(os.O_WRONLY))
        space.set_const(w_cls, "RDWR", space.newint(os.O_RDWR))
        space.set_const(w_cls, "APPEND", space.newint(os.O_APPEND))
        space.set_const(w_cls, "CREAT", space.newint(os.O_CREAT))
        space.set_const(w_cls, "EXCL", space.newint(os.O_EXCL))
        space.set_const(w_cls, "TRUNC", space.newint(os.O_TRUNC))

        space.set_const(w_cls, "Stat", space.getclassfor(W_FileStatObject))

    @classdef.singleton_method("allocate")
    def method_allocate(self, space, args_w):
        return W_FileObject(space)

    @classdef.singleton_method("size?", name="path")
    def singleton_method_size_p(self, space, name):
        try:
            stat_val = os.stat(name)
        except OSError:
            return space.w_nil
        return space.w_nil if stat_val.st_size == 0 else space.newint_or_bigint(stat_val.st_size)

    @classdef.singleton_method("unlink")
    @classdef.singleton_method("delete")
    def singleton_method_delete(self, space, args_w):
        for w_path in args_w:
            path = Coerce.path(space, w_path)
            try:
                os.unlink(path)
            except OSError as e:
                raise error_for_oserror(space, e)
        return space.newint(len(args_w))

    @classdef.method("initialize", filename="path")
    def method_initialize(self, space, filename, w_mode=None, w_perm_or_opt=None, w_opt=None):
        if w_mode is None:
            w_mode = space.w_nil
        if w_perm_or_opt is None:
            w_perm_or_opt = space.w_nil
        if w_opt is None:
            w_opt = space.w_nil
        if isinstance(w_perm_or_opt, W_HashObject):
            assert w_opt is space.w_nil
            perm = 0665
            w_opt = w_perm_or_opt
        elif w_opt is not space.w_nil:
            perm = space.int_w(w_perm_or_opt)
        else:
            perm = 0665
        mode = map_filemode(space, w_mode)
        if w_perm_or_opt is not space.w_nil or w_opt is not space.w_nil:
            raise space.error(space.w_NotImplementedError, "options hash or permissions for File.new")
        try:
            self.fd = os.open(filename, mode, perm)
        except OSError as e:
            raise error_for_oserror(space, e)
        return self

    @classdef.singleton_method("dirname", path="path")
    def method_dirname(self, space, path):
        if "/" not in path:
            return space.newstr_fromstr(".")
        idx = path.rfind("/")
        while idx > 0 and path[idx - 1] == "/":
            idx -= 1
        if idx == 0:
            return space.newstr_fromstr("/")
        assert idx >= 0
        return space.newstr_fromstr(path[:idx])

    @classdef.singleton_method("expand_path", path="path")
    def method_expand_path(self, space, path, w_dir=None):
        if path and path[0] == "~":
            if len(path) >= 2 and path[1] == "/":
                path = os.environ["HOME"] + path[1:]
            elif len(path) < 2:
                return space.newstr_fromstr(os.environ["HOME"])
            else:
                raise NotImplementedError
        elif not path or path[0] != "/":
            if w_dir is not None and w_dir is not space.w_nil:
                dir = space.str_w(space.send(self, space.newsymbol("expand_path"), [w_dir]))
            else:
                dir = os.getcwd()

            path = dir + "/" + path

        items = []
        parts = path.split("/")
        for part in parts:
            if part == "..":
                items.pop()
            elif part and part != ".":
                items.append(part)

        if not items:
            return space.newstr_fromstr("/")
        return space.newstr_fromstr("/" + "/".join(items))

    @classdef.singleton_method("join")
    def singleton_method_join(self, space, args_w):
        sep = space.str_w(space.find_const(self, "SEPARATOR"))
        result = []
        for w_arg in args_w:
            if isinstance(w_arg, W_ArrayObject):
                ec = space.getexecutioncontext()
                with ec.recursion_guard("file_singleton_method_join", w_arg) as in_recursion:
                    if in_recursion:
                        raise space.error(space.w_ArgumentError, "recursive array")
                    string = space.str_w(
                        space.send(space.getclassfor(W_FileObject), space.newsymbol("join"), space.listview(w_arg))
                    )
            else:
                w_string = space.convert_type(w_arg, space.w_string, "to_path", raise_error=False)
                if w_string is space.w_nil:
                    w_string = space.convert_type(w_arg, space.w_string, "to_str")
                string = space.str_w(w_string)

            if string == "" and len(args_w) > 1:
                if (not result) or result[-1] != sep:
                    result += sep
            if string.startswith(sep):
                while result and result[-1] == sep:
                    result.pop()
            elif result and not result[-1] == sep:
                result += sep
            result += string
        return space.newstr_fromchars(result)

    @classdef.singleton_method("exists?", filename="path")
    @classdef.singleton_method("exist?", filename="path")
    def method_existp(self, space, filename):
        return space.newbool(os.path.exists(filename))

    @classdef.singleton_method("file?", filename="path")
    def method_filep(self, space, filename):
        return space.newbool(os.path.isfile(filename))

    @classdef.singleton_method("directory?", filename="path")
    def method_directoryp(self, space, filename):
        return space.newbool(isdir(filename))

    @classdef.singleton_method("symlink?", filename="path")
    def method_symlinkp(self, space, filename):
        return space.newbool(os.path.islink(filename))

    @classdef.singleton_method("executable?", filename="path")
    def method_executablep(self, space, filename):
        return space.newbool(os.path.isfile(filename) and os.access(filename, os.X_OK))

    @classdef.singleton_method("identical?", file="path", other="path")
    def method_identicalp(self, space, file, other):
        try:
            file_stat = os.stat(file)
            other_stat = os.stat(other)
        except OSError:
            return space.w_false
        return space.newbool(file_stat.st_dev == other_stat.st_dev and
                file_stat.st_ino == other_stat.st_ino)

    @classdef.singleton_method("basename", filename="path")
    def method_basename(self, space, filename):
        i = filename.rfind("/") + 1
        assert i >= 0
        return space.newstr_fromstr(filename[i:])

    @classdef.singleton_method("umask", mask="int")
    def method_umask(self, space, mask=-1):
        if mask >= 0:
            return space.newint(os.umask(mask))
        else:
            current_umask = os.umask(0)
            os.umask(current_umask)
            return space.newint(current_umask)

    @classdef.method("truncate", length="int")
    def method_truncate(self, space, length):
        self.ensure_not_closed(space)
        ftruncate(self.fd, length)
        return space.newint(0)

    @classdef.method("chmod", mode="int")
    def method_chmod(self, space, mode):
        try:
            fchmod(self.fd, mode)
        except OSError as e:
            raise error_for_oserror(space, e)
        return space.newint(0)

    @classdef.singleton_method("chmod", mode="int")
    def singleton_method_chmod(self, space, mode, args_w):
        for arg_w in args_w:
            path = Coerce.path(space, arg_w)
            try:
                os.chmod(path, mode)
            except OSError as e:
                raise error_for_oserror(space, e)
        return space.newint(len(args_w))

    @classdef.singleton_method("stat", filename="path")
    def singleton_method_stat(self, space, filename):
        try:
            stat_val = os.stat(filename)
        except OSError as e:
            raise error_for_oserror(space, e)
        stat_obj = W_FileStatObject(space)
        stat_obj.set_stat(stat_val)
        return stat_obj

    @classdef.singleton_method("lstat", filename="path")
    def singleton_method_lstat(self, space, filename):
        try:
            stat_val = os.lstat(filename)
        except OSError as e:
            raise error_for_oserror(space, e)
        stat_obj = W_FileStatObject(space)
        stat_obj.set_stat(stat_val)
        return stat_obj

    if IS_WINDOWS:
        classdef.s_notimplemented("symlink")
        classdef.s_notimplemented("link")
    else:
        @classdef.singleton_method("symlink", old_name="path", new_name="path")
        def singleton_method_symlink(self, space, old_name, new_name):
            try:
                os.symlink(old_name, new_name)
            except OSError as e:
                raise error_for_oserror(space, e)
            return space.newint(0)

        @classdef.singleton_method("link", old_name="path", new_name="path")
        def singleton_method_link(self, space, old_name, new_name):
            try:
                os.link(old_name, new_name)
            except OSError as e:
                raise error_for_oserror(space, e)
            return space.newint(0)


class W_FileStatObject(W_Object):
    classdef = ClassDef("Stat", W_Object.classdef, filepath=__file__)

    def __init__(self, space):
        W_Object.__init__(self, space)
        self.is_initialized = False

    def set_stat(self, stat):
        self._stat = stat
        self.is_initialized = True

    def get_stat(self, space):
        if not self.is_initialized:
            raise space.error(space.w_RuntimeError, "uninitialized File::Stat")
        return self._stat

    @classdef.singleton_method("allocate")
    def singleton_method_allocate(self, space, w_args):
        return W_FileStatObject(space)

    @classdef.method("initialize", filename="path")
    def method_initialize(self, space, filename):
        try:
            self.set_stat(os.stat(filename))
        except OSError as e:
            raise error_for_oserror(space, e)

    @classdef.method("blockdev?")
    def method_blockdevp(self, space):
        return space.newbool(stat.S_ISBLK(self.get_stat(space).st_mode))

    if IS_WINDOWS:
        def unsupported_attr(name, classdef):
            @classdef.method(name)
            def method(self, space):
                return space.w_nil
            method.__name__ = name
            return method
        method_blksize = unsupported_attr("blksize", classdef)
        method_blocks = unsupported_attr("blocks", classdef)
        method_rdev = unsupported_attr("rdev", classdef)
    else:
        @classdef.method("blksize")
        def method_blksize(self, space):
            return space.newint(self.get_stat(space).st_blksize)

        @classdef.method("rdev")
        def method_rdev(self, space):
            return space.newint(self.get_stat(space).st_rdev)

        @classdef.method("blocks")
        def method_blocks(self, space):
            return space.newint(self.get_stat(space).st_blocks)

    @classdef.method("chardev?")
    def method_chardevp(self, space):
        return space.newbool(stat.S_ISCHR(self.get_stat(space).st_mode))

    @classdef.method("dev")
    def method_dev(self, space):
        return space.newint_or_bigint(self.get_stat(space).st_dev)

    @classdef.method("directory?")
    def method_directoryp(self, space):
        return space.newbool(stat.S_ISDIR(self.get_stat(space).st_mode))

    @classdef.method("file?")
    def method_filep(self, space):
        return space.newbool(stat.S_ISREG(self.get_stat(space).st_mode))

    @classdef.method("ftype")
    def method_ftype(self, space):
        stat_val = self.get_stat(space)
        if stat.S_ISREG(stat_val.st_mode):
            return space.newstr_fromstr("file")
        elif stat.S_ISDIR(stat_val.st_mode):
            return space.newstr_fromstr("directory")
        elif stat.S_ISCHR(stat_val.st_mode):
            return space.newstr_fromstr("characterSpecial")
        elif stat.S_ISBLK(stat_val.st_mode):
            return space.newstr_fromstr("blockSpecial")
        elif stat.S_ISFIFO(stat_val.st_mode):
            return space.newstr_fromstr("fifo")
        elif stat.S_ISLNK(stat_val.st_mode):
            return space.newstr_fromstr("link")
        elif stat.S_ISSOCK(stat_val.st_mode):
            return space.newstr_fromstr("socket")
        else:
            return space.newstr_fromstr("unknown")

    @classdef.method("gid")
    def method_gid(self, space):
        return space.newint(self.get_stat(space).st_gid)

    @classdef.method("ino")
    def method_ino(self, space):
        return space.newint_or_bigint(self.get_stat(space).st_ino)

    def get_w_mode(self, space):
        return space.newint(self.get_stat(space).st_mode)

    @classdef.method("mode")
    def method_mode(self, space):
        return self.get_w_mode(space)

    @classdef.method("nlink")
    def method_nlink(self, space):
        return space.newint(self.get_stat(space).st_nlink)

    @classdef.method("setgid?")
    def method_setgidp(self, space):
        return space.newbool(stat.S_IMODE(self.get_stat(space).st_mode) & stat.S_ISGID)

    @classdef.method("setuid?")
    def method_setuidp(self, space):
        return space.newbool(stat.S_IMODE(self.get_stat(space).st_mode) & stat.S_ISUID)

    @classdef.method("size")
    def method_size(self, space):
        return space.newint_or_bigint(self.get_stat(space).st_size)

    @classdef.method("socket?")
    def method_socketp(self, space):
        return space.newbool(stat.S_ISSOCK(self.get_stat(space).st_mode))

    @classdef.method("sticky?")
    def method_stickyp(self, space):
        return space.newbool(stat.S_IMODE(self.get_stat(space).st_mode) & stat.S_ISVTX)

    @classdef.method("symlink?")
    def method_symlinkp(self, space):
        return space.newbool(stat.S_ISLNK(self.get_stat(space).st_mode))

    @classdef.method("uid")
    def method_uid(self, space):
        return space.newint(self.get_stat(space).st_uid)

    @classdef.method("world_readable?")
    def method_world_readablep(self, space):
        if stat.S_IMODE(self.get_stat(space).st_mode) & stat.S_IROTH:
            return self.get_w_mode(space)
        return space.w_nil

    @classdef.method("world_writable?")
    def method_world_writablep(self, space):
        if stat.S_IMODE(self.get_stat(space).st_mode) & stat.S_IWOTH:
            return self.get_w_mode(space)
        return space.w_nil
