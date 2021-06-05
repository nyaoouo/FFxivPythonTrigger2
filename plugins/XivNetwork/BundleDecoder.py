import time
from struct import pack
from ctypes import sizeof
from threading import Lock
from traceback import format_exc
from typing import Optional
from zlib import decompress, compress, MAX_WBITS, error
from socket import ntohl
from datetime import datetime, timedelta, timezone
from queue import Queue

from FFxivPythonTrigger.Logger import Logger

from plugins.XivNetwork.Structs import FFXIVBundleHeader

_logger = Logger("XivNetwork/BundleDecoder")

MAGIC_NUMBER = 0x41a05252
MAGIC_NUMBER_Array = pack('I', MAGIC_NUMBER)

_encoding_error = False

magics = {
    'magic0': None,
    'magic1': None,
    'magic2': None,
    'magic3': None,
}

header_size = sizeof(FFXIVBundleHeader)


def decompress_message(header: FFXIVBundleHeader, buffer: bytearray) -> Optional[bytearray]:
    if header.encoding == 0x0000 or header.encoding == 0x0001:
        return buffer[header_size:header.length]
    if header.encoding != 0x0101 and header.encoding != 0x0100:
        global _encoding_error
        if not _encoding_error:
            _logger.error("unknown encoding type:", hex(header.encoding))
            _encoding_error = True
        return None
    try:
        return bytearray(decompress(buffer[header_size + 2:header.length], wbits=-MAX_WBITS))
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
    message_raw = decompress_message(header, raw)
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
    x = header is None
    if header is None:
        header = FFXIVBundleHeader(**magics, epoch=int(time.time() * 1000), )
    new_raw_message = bytearray()
    for m in messages: new_raw_message += m
    new_msg = compress_message(header, new_raw_message)
    if new_msg is None: return
    header.length = len(new_msg) + header_size
    header.msg_count = len(messages)
    ans = bytearray(header) + new_msg
    # h, m = extract_single(ans)
    # _logger(h, m[0].hex())
    return ans


class BundleDecoder(object):

    # messages: list[tuple[int, bytearray]]

    def __init__(self, recall: callable):
        self.data = Queue()
        self._buffer = bytearray()
        self.recall = recall
        self.messages = Queue()
        self.work = False
        self.is_processing = False

    def store_data(self, data: bytearray):
        self.data.put(data)

    def stop_process(self):
        self.work = False
        self.data.put(bytearray())
        while self.is_processing:
            time.sleep(0.05)

    def process(self):
        self.work = True
        self.is_processing = True
        try:
            while self.work:
                self._buffer = self._buffer+self.data.get()
                while len(self._buffer):
                    if len(self._buffer) < header_size:
                        break
                    header = FFXIVBundleHeader.from_buffer(self._buffer)
                    if header.magic0 != MAGIC_NUMBER and header.magic0 and header.magic1 and header.magic2 and header.magic3:
                        _logger.error("Invalid magic in header:", header.get_data())
                        self.reset_stream()
                        continue
                    if header.length > len(self._buffer):
                        break
                    if header.magic0:
                        for key in magics.keys():
                            magics[key] = getattr(header, key)
                    message = decompress_message(header, self._buffer)
                    if message is None:
                        self.reset_stream()
                    else:
                        self._buffer = self._buffer[header.length:]
                        if len(message):
                            try:
                                msg_offset = 0
                                msg_time = datetime.fromtimestamp(header.epoch / 1000)
                                # _logger.debug(f"{header.msg_count} in {len(message)} long [{bytearray(header).hex()}]")
                                for i in range(header.msg_count):
                                    msg_len = int.from_bytes(message[msg_offset:msg_offset + 4], byteorder='little')
                                    self.recall(msg_time, message[msg_offset:msg_offset + msg_len])
                                    msg_offset += msg_len
                            except Exception:
                                _logger.error("Split message error:\n", format_exc())
                                self._buffer.clear()
                                break

        except Exception:
            self.is_processing = False
            raise
        self.is_processing = False

    def reset_stream(self):
        try:
            idx = self._buffer.index(MAGIC_NUMBER_Array,1)
        except ValueError:
            self._buffer.clear()
        else:
            self._buffer = self._buffer[idx:]
