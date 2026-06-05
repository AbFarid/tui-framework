from __future__ import annotations
import sys
import functools

DEFAULT_PATH = 'debug.log'


class DebugLog:
    """A drop-in `sys.stdout` replacement that appends writes to a file."""

    def __init__(self, path: str = DEFAULT_PATH):
        self.path = path
        self._buf = ''

    def write(self, text: str):
        self._buf += text
        while '\n' in self._buf:
            line, self._buf = self._buf.split('\n', 1)
            with open(self.path, 'a') as f:
                f.write(line + '\n')

    def flush(self):
        if self._buf:
            with open(self.path, 'a') as f:
                f.write(self._buf)
            self._buf = ''


_real_stdout = None


def install(path: str = DEFAULT_PATH, mode='w'):
    if mode not in ('a', 'w'): mode = 'w'
    global _real_stdout
    _real_stdout = sys.stdout
    with open(path, mode): pass
    sys.stdout = DebugLog(path)
    return _real_stdout


def restore():
    global _real_stdout
    if _real_stdout is not None:
        sys.stdout = _real_stdout
        _real_stdout = None


def traced(fn):  # requirement: custom decorator
    """Log every call to the decorated method (args minus self) to the debug log."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        print(f'→ {fn.__name__}({", ".join(map(str, args[1:]))})')
        return fn(*args, **kwargs)
    return wrapper


def tree(cls):
    """Class decorator: dump the object's widget tree once it finishes building."""
    orig_init = cls.__init__
    @functools.wraps(orig_init)
    def __init__(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.tree()
    cls.__init__ = __init__
    return cls
