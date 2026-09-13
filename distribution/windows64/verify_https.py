"""Exercise the shipped libcurl with Windows certificate verification enabled."""
import ctypes as c
import json
import os
from pathlib import Path
import sys


def verify(directory):
    if sys.platform != 'win32' or c.sizeof(c.c_void_p) != 8:
        raise RuntimeError('This runtime check requires native Windows x64 Python')
    directory = Path(directory).resolve()
    # Test the library's real default, without a developer-machine override.
    saved_backend = os.environ.pop('CURL_SSL_BACKEND', None)
    try:
        with os.add_dll_directory(str(directory)):
            curl = c.CDLL(str(directory / 'libcurl.dll'))
            curl.curl_version.restype = c.c_char_p
            version = curl.curl_version().decode('ascii')
            if 'Schannel' not in version or 'OpenSSL' in version:
                raise RuntimeError('Expected the native Windows TLS backend: ' + version)
            curl.curl_global_init.argtypes = [c.c_long]
            curl.curl_global_init.restype = c.c_int
            if curl.curl_global_init(3) != 0:
                raise RuntimeError('curl global initialization failed')
            curl.curl_easy_init.restype = c.c_void_p
            curl.curl_easy_setopt.argtypes = [c.c_void_p, c.c_int]
            curl.curl_easy_setopt.restype = c.c_int
            curl.curl_easy_perform.argtypes = [c.c_void_p]
            curl.curl_easy_perform.restype = c.c_int
            curl.curl_easy_cleanup.argtypes = [c.c_void_p]
            curl.curl_easy_strerror.argtypes = [c.c_int]
            curl.curl_easy_strerror.restype = c.c_char_p
            handle = curl.curl_easy_init()
            if not handle:
                curl.curl_global_cleanup()
                raise RuntimeError('curl easy initialization failed')
            received = 0

            @c.CFUNCTYPE(c.c_size_t, c.c_void_p, c.c_size_t, c.c_size_t, c.c_void_p)
            def receive(_data, size, count, _user):
                nonlocal received
                length = size * count
                received += length
                return length

            url = (b'https://raw.githubusercontent.com/pob220/OpenCPN-Chart-Aware/'
                   b'preview/windows-x64/distribution/windows64/dependencies.json')
            try:
                # URL, WRITEFUNCTION, TIMEOUT, FAILONERROR, SSL_VERIFYPEER,
                # SSL_VERIFYHOST, and USERAGENT from curl's public API.
                for option, value in (
                    (10002, c.c_char_p(url)), (20011, receive),
                    (13, c.c_long(30)), (45, c.c_long(1)),
                    (64, c.c_long(1)), (81, c.c_long(2)),
                    (10018, c.c_char_p(b'OpenCPN-Windows64-Preview-CI')),
                ):
                    result = curl.curl_easy_setopt(handle, option, value)
                    if result:
                        raise RuntimeError(curl.curl_easy_strerror(result).decode())
                result = curl.curl_easy_perform(handle)
                if result:
                    raise RuntimeError(curl.curl_easy_strerror(result).decode())
                if not received:
                    raise RuntimeError('HTTPS returned an empty response')
                return {'curl': version, 'verified_https': True, 'bytes': received}
            finally:
                curl.curl_easy_cleanup(handle)
                curl.curl_global_cleanup()
    finally:
        if saved_backend is not None:
            os.environ['CURL_SSL_BACKEND'] = saved_backend


if __name__ == '__main__':
    print(json.dumps(verify(sys.argv[1]), indent=2))
