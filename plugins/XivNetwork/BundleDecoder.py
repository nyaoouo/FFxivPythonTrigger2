from ctypes import sizeof
from threading import Lock
from traceback import format_exc
from typing import Optional
from zlib import decompress, MAX_WBITS
from socket import ntohl
from datetime import datetime, timedelta, timezone

from FFxivPythonTrigger.Logger import Logger

from .Structs import FFXIVBundleHeader

_logger = Logger("XivNetwork/BundleDecoder")

MAGIC_NUMBER = bytearray(b"\x52\x52\xa0\x41")

_encoding_error = False

invalid_headers = set()

min_datetime = datetime(1970, 1, 1).replace(tzinfo=timezone.utc).astimezone(tz=None)


def ntohll(host):
    return ntohl(host & 0xFFFFFFFF) << 32 | ntohl((host >> 32) & 0xFFFFFFFF)


header_size = sizeof(FFXIVBundleHeader)


def decompress_message(header: FFXIVBundleHeader, buffer: bytearray, offset: int) -> Optional[bytearray]:
    if header.encoding == 0x0000 or header.encoding == 0x0001:
        return buffer[offset + header_size:offset + header.length]
    if header.encoding != 0x0101 and header.encoding != 0x0100:
        global _encoding_error
        if not _encoding_error:
            _logger.error("unknown encoding type:", hex(header.encoding))
            _encoding_error = True
        return None
    try:
        return bytearray(decompress(buffer[offset + header_size + 2:offset + header.length], wbits=-MAX_WBITS))
    except Exception:
        _logger.error("Decompression error:\n", format_exc())


class BundleDecoder(object):
    _buffer: bytearray
    messages: list[tuple[int, bytearray]]

    def __init__(self):
        self._buffer = bytearray()
        self.messages = list()
        self.lock = Lock()

    def store_data(self, data: bytearray):
        self._buffer += data
        if self.lock.acquire(False):
            self.process_buffer()
            self.lock.release()
            return True
        else:
            return False

    def process_buffer(self):
        offset = 0
        while len(self._buffer) and offset < len(self._buffer):
            header = FFXIVBundleHeader.from_buffer(self._buffer[offset:])
            if header.magic0 != 0x41a05252 and header.magic0 and header.magic1 and header.magic2 and header.magic3:
                raw = self._buffer[offset:offset + header_size].hex()
                if raw not in invalid_headers:
                    _logger.error("Invalid magic # in header:", raw)
                    invalid_headers.add(raw)
                offset = self.reset_stream(offset)
                continue
            if header.length > len(self._buffer) - offset:
                if 0 < offset != len(self._buffer):
                    self._buffer = self._buffer[offset:]
                return
            message = decompress_message(header, self._buffer, offset)
            if message is None:
                offset = self.reset_stream(offset)
                continue
            offset += header.length
            if offset == len(self._buffer):
                self._buffer.clear()
            if not len(message):
                continue
            try:
                msg_offset = 0
                msg_time = min_datetime + timedelta(milliseconds=ntohll(header.epoch))
                #_logger.debug(f"{header.msg_count} in {header.length} long")
                for i in range(header.msg_count):
                    msg_len = int.from_bytes(message[msg_offset:msg_offset + 2], byteorder='little')
                    self.messages.append((msg_time, message[msg_offset:msg_offset + msg_len]))
                    msg_offset += msg_len
            except Exception:
                _logger.error("Split message error:\n", format_exc())
                self._buffer.clear()
                return

    def get_next_message(self):
        if self.messages:
            return self.messages.pop(0)
        else:
            return None

    def reset_stream(self, offset: int) -> int:
        try:
            ans=self._buffer.index(MAGIC_NUMBER, offset)
            return ans
        except ValueError:
            self._buffer.clear()
            return -1
