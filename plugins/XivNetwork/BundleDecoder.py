import time
from struct import pack
from ctypes import sizeof
from threading import Lock
from traceback import format_exc
from typing import Optional
from zlib import decompress, compress, MAX_WBITS, error
from socket import ntohl
from datetime import datetime, timedelta, timezone

from FFxivPythonTrigger.Logger import Logger

from plugins.XivNetwork.Structs import FFXIVBundleHeader

_logger = Logger("XivNetwork/BundleDecoder")

MAGIC_NUMBER = 0x41a05252
MAGIC_NUMBER_Array = pack('I', MAGIC_NUMBER)

_encoding_error = False

invalid_headers = set()

min_datetime = datetime(1970, 1, 1).replace(tzinfo=timezone.utc).astimezone(tz=None)

magics = {
    'magic0': None,
    'magic1': None,
    'magic2': None,
    'magic3': None,
}


def ntohll(host):
    return ntohl(host & 0xFFFFFFFF) << 32 | ntohl((host >> 32) & 0xFFFFFFFF)


header_size = sizeof(FFXIVBundleHeader)

t = list()


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
    except error:
        _logger.error("Decompression error:\n", format_exc())


def compress_message(header: FFXIVBundleHeader, message: bytearray):
    if header.encoding == 0x0000 or header.encoding == 0x0001:
        return message
    elif header.encoding == 0x0101 or header.encoding == 0x0100:
        return bytearray(compress(message)[2:])
    else:
        _logger.error("Unknown encoding type:", hex(header.encoding))
        return None


def extract_single(raw: bytearray):
    if len(raw) < header_size: return
    header = FFXIVBundleHeader.from_buffer(raw)
    if header.magic0 != 0x41a05252 and header.magic0 and header.magic1 and header.magic2 and header.magic3:
        _logger.error("[single] Invalid magic # in header:", raw[:header_size])
        return
    if header.length > len(raw):
        _logger.error(f"[single] Invalid msg length({len(raw)}/{header.length})")
        return
    message_raw = decompress_message(header, raw, 0)
    if message_raw is None or not len(message_raw): return
    try:
        messages = list()
        msg_offset = 0
        for i in range(header.msg_count):
            msg_len = int.from_bytes(message_raw[msg_offset:msg_offset + 4], byteorder='little')
            messages.append(message_raw[msg_offset:msg_offset + msg_len])
            msg_offset += msg_len
        return header, messages
    except Exception:
        _logger.error("[single] Split message error:\n", format_exc())
        return


def pack_single(header: Optional[FFXIVBundleHeader], messages: list[bytearray]):
    x=header is None
    if header is None:
        header = FFXIVBundleHeader(**magics,epoch=int(time.time()*1000),)
    new_raw_message = bytearray()
    for m in messages: new_raw_message += m
    new_msg = compress_message(header, new_raw_message)
    if new_msg is None: return
    header.length = len(new_msg)+header_size
    header.msg_count = len(messages)
    ans=bytearray(header) + new_msg
    # h, m = extract_single(ans)
    # _logger(h, m[0].hex())
    return ans


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
            if len(self._buffer) - offset <= header_size:
                offset = self.reset_stream(offset)
                continue
            header = FFXIVBundleHeader.from_buffer(self._buffer[offset:])
            if header.magic0 != MAGIC_NUMBER and header.magic0 and header.magic1 and header.magic2 and header.magic3:
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
            if header.magic0:
                magics["magic0"] = header.magic0
                magics['magic1'] = header.magic1
                magics['magic2'] = header.magic2
                magics['magic3'] = header.magic3
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
                msg_time = datetime.fromtimestamp(header.epoch / 1000)
                # _logger.debug(f"{header.msg_count} in {len(message)} long [{bytearray(header).hex()}]")
                for i in range(header.msg_count):
                    msg_len = int.from_bytes(message[msg_offset:msg_offset + 4], byteorder='little')
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
            ans = self._buffer.index(MAGIC_NUMBER_Array, offset + 1)
            return ans
        except ValueError:
            self._buffer.clear()
            return -1
