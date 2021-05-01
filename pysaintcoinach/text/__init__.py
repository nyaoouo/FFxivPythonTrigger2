from typing import Dict, Callable, Tuple, List, Union
import os
from functools import total_ordering
import io
import struct

from .utils import TagType, DecodeExpressionType, IntegerType, NodeFlags
from .nodes import INode, IExpressionNode, INodeWithChildren
from .expressions import ExpressionCollection


VALID_TAGS = list(map(lambda x: x.value, TagType.__members__.values()))

@total_ordering
class XivString(IExpressionNode, INodeWithChildren):
    @property
    @classmethod
    def empty(cls): return cls([])

    @property
    def tag(self): return TagType.none

    @property
    def flags(self): return NodeFlags.HasChildren | NodeFlags.IsExpression

    @property
    def children(self): return self.__children

    @property
    def is_empty(self) -> bool:
        if len(self.__children) == 0:
            return True
        return len(str(self).strip()) != 0

    def __init__(self, *args):
        self.__children = list(*args)
        self.__string_cache = None

    def __str__(self):
        if self.__string_cache is not None:
            return self.__string_cache
        s = ''.join(map(str, self.children))
        self.__string_cache = s
        return s

    def __hash__(self):
        return hash(str(self))

    def __eq__(self, other):
        if isinstance(other, XivString):
            return str(self) == str(other)
        elif isinstance(other, str):
            return str(self) == other
        else:
            return False

    def __lt__(self, other):
        if isinstance(other, XivString):
            return str(self) < str(other)
        elif isinstance(other, str):
            return str(self) < other
        else:
            return NotImplemented

    def evaluate(self, parameters):
        return ExpressionCollection(*[c.evaluate(parameters) for c in self.children])

    def accept(self, visitor):
        return visitor.visit(self)


def _read_byte(stream: io.BytesIO) -> int:
    return struct.unpack_from('B', stream.read(1))[0]


class XivStringDecoder(object):
    TAG_START_MARKER = 0x02
    TAG_END_MARKER = 0x03

    TagDecoder = Callable[['XivStringDecoder', io.BytesIO, TagType, int], INode]

    __default = None

    @classmethod
    def default(cls) -> 'XivStringDecoder':
        if cls.__default is None:
            cls.__default = cls()
        return cls.__default

    @property
    def encoding(self): return self.__encoding

    @encoding.setter
    def encoding(self, value): self.__encoding = value

    @property
    def default_tag_decoder(self) -> TagDecoder:
        return self.__default_tag_decoder

    @default_tag_decoder.setter
    def default_tag_decoder(self, value):
        if value is None:
            raise ValueError('value is None')
        self.__default_tag_decoder = value

    @property
    def dash(self): return self.__dash

    @dash.setter
    def dash(self, value): self.__dash = value

    @property
    def new_line(self): return self.__new_line

    @new_line.setter
    def new_line(self, value): self.__new_line = value

    def __init__(self):
        self.__dash = '-'
        self.__new_line = os.linesep
        self.__tag_decoders = {}  # type: Dict[TagType, 'TagDecoder']

        self.__default_tag_decoder = self._decode_tag_default

        # For now, these need to use Enum.value so existing scripts remain compatible.
        self.set_decoder(TagType.Clickable.value,
                         lambda i,t,l: self._decode_generic_element_with_variable_arguments(i, t, l, 1, 0x7fffffff))
        self.set_decoder(TagType.Color.value, self._decode_color)
        self.set_decoder(TagType.Color2.value, self._decode_color)
        self.set_decoder(TagType.CommandIcon.value,
                         lambda i,t,l: self._decode_generic_element(i, t, l, 1, False))
        self.set_decoder(TagType.Dash.value, lambda i,t,l: nodes.StaticString(self.dash))
        self.set_decoder(TagType.DecimalValue.value, lambda i,t,l: self._decode_generic_element(i, t, l, 0, True))
        self.set_decoder(TagType.Emphasis.value, self._decode_generic_surrounding_tag)
        self.set_decoder(TagType.Emphasis2.value, self._decode_generic_surrounding_tag)
        # TODO: Fixed
        self.set_decoder(TagType.Format.value, self._decode_format)
        self.set_decoder(TagType.Gui.value, lambda i,t,l: self._decode_generic_element(i, t, l, 1, False))
        self.set_decoder(TagType.Highlight.value, lambda i,t,l: self._decode_generic_element(i, t, l, 0, True))
        self.set_decoder(TagType.If.value, self._decode_if)
        self.set_decoder(TagType.IfEquals.value, self._decode_if_equals)
        self.set_decoder(TagType.IfSelf.value, self._decode_if_self)
        # Indent
        self.set_decoder(TagType.InstanceContent.value, lambda i,t,l: self._decode_generic_element(i, t, l, 0, True))
        self.set_decoder(TagType.LineBreak.value, lambda i,t,l: nodes.StaticString(self.new_line))
        self.set_decoder(TagType.Name.value, lambda i,t,l: self._decode_generic_element(i, t, l, 1, False))
        self.set_decoder(TagType.OrdinalNumber.value, lambda i,t,l: self._decode_generic_element(i, t, l, 1, False))
        self.set_decoder(TagType.Sfx.value, lambda i, t, l: self._decode_generic_element(i, t, l, 1, False))
        # Sheets
        # Sheet name, Row[, Column[, Parameters]+]
        self.set_decoder(TagType.Sheet.value,
                         lambda i,t,l: self._decode_generic_element_with_variable_arguments(i, t, l, 2, 0x7fffffff))
        # Sheet name, Attributive row, Sheet row[, Sheet column[, Attributive index[, Parameters]+]
        self.set_decoder(TagType.SheetDe.value,
                         lambda i,t,l: self._decode_generic_element_with_variable_arguments(i, t, l, 3, 0x7fffffff))
        self.set_decoder(TagType.SheetEn.value,
                         lambda i,t,l: self._decode_generic_element_with_variable_arguments(i, t, l, 3, 0x7fffffff))
        self.set_decoder(TagType.SheetFr.value,
                         lambda i,t,l: self._decode_generic_element_with_variable_arguments(i, t, l, 3, 0x7fffffff))
        self.set_decoder(TagType.SheetJa.value,
                         lambda i,t,l: self._decode_generic_element_with_variable_arguments(i, t, l, 3, 0x7fffffff))
        self.set_decoder(TagType.Split.value, lambda i,t,l: self._decode_generic_element(i, t, l, 3, False))
        self.set_decoder(TagType.Switch.value, self._decode_switch)
        self.set_decoder(TagType.Time.value, lambda i,t,l: self._decode_generic_element(i, t, l, 1, False))
        self.set_decoder(TagType.TwoDigitValue.value, lambda i,t,l: self._decode_generic_element(i, t, l, 1, False))
        # Unknowns
        self.set_decoder(TagType.UIForeground.value, self._decode_ui_color)
        self.set_decoder(TagType.UIGlow.value, self._decode_ui_color)
        self.set_decoder(TagType.Value.value,
                         lambda i,t,l: self._decode_generic_element(i, t, l, 1, False))
        self.set_decoder(TagType.ZeroPaddedValue.value, self._decode_zero_padded_value)

        self.set_decoder(TagType.Unknown2D.value,
                         lambda i,t,l: self._decode_generic_element(i, t, l, 0, True))
        self.set_decoder(TagType.Unknown2F.value,
                         lambda i,t,l: self._decode_generic_element(i, t, l, 0, True))

    def set_decoder(self, tag: TagType, decoder: TagDecoder):
        self.__tag_decoders[tag] = decoder

    def decode(self, buffer: Union[bytes, io.BytesIO], length: int = None) -> XivString:
        if isinstance(buffer, bytes):
            input = io.BytesIO(buffer)
            length = len(buffer)
        else:
            input = buffer

        if length < 0:
            raise ValueError('length')
        end = input.tell() + length
        if end > len(input.getbuffer()):
            raise ValueError('length')

        parts = []  # type: List[INode]
        pending_static = bytearray()

        while input.tell() < end:
            v = _read_byte(input)
            if v == self.TAG_START_MARKER:
                self._add_static(pending_static, parts)
                parts += [self._decode_tag(input)]
                if input.tell() > end:
                    raise EOFError
            else:
                pending_static += bytes([v])

        self._add_static(pending_static, parts)
        return XivString(parts)

    def _decode_tag(self, input: io.BytesIO):
        tag = _read_byte(input)
        length = self._get_integer(input)
        end = input.tell() + length
        if tag not in VALID_TAGS:
            raise ValueError('Unknown TagType: 0x%02X' % tag)
        tag = TagType(tag)
        decoder = None  # type: 'TagDecoder'
        decoder = self.__tag_decoders.get(tag.value, self.default_tag_decoder)
        result = decoder(input, tag, length)
        if input.tell() != end:
            input.seek(end)
        if _read_byte(input) != self.TAG_END_MARKER:
            raise RuntimeError('Invalid Data')
        return result

    def _add_static(self, pending: bytearray, target_parts: List[INode]):
        if len(pending) == 0:
            return
        target_parts += [nodes.StaticString(pending.decode())]
        pending.clear()

    def _decode_tag_default(self, input: io.BytesIO, tag: TagType, length: int) -> INode:
        return nodes.DefaultElement(tag, input.read(length))

    def _decode_expression(self, input: io.BytesIO, expr_type: DecodeExpressionType = None) -> INode:
        if expr_type is None:
            expr_type = _read_byte(input)
        t = expr_type  # type: int
        if t < 0xD0:
            return nodes.StaticInteger(t - 1)
        if t < 0xE0:
            return nodes.TopLevelParameter(t - 1)

        if isinstance(expr_type, int):
            expr_type = DecodeExpressionType(expr_type)

        if expr_type == DecodeExpressionType.Decode:
            return self.decode(input, self._get_integer(input))
        elif expr_type == DecodeExpressionType.Byte:
            return nodes.StaticInteger(self._get_integer(input, IntegerType.Byte))
        elif expr_type == DecodeExpressionType.Int16_MinusOne:
            return nodes.StaticInteger(self._get_integer(input, IntegerType.Int16) - 1)
        elif expr_type == DecodeExpressionType.Int16_1 or expr_type == DecodeExpressionType.Int16_2:
            return nodes.StaticInteger(self._get_integer(input, IntegerType.Int16))
        elif expr_type == DecodeExpressionType.Int24_MinusOne:
            return nodes.StaticInteger(self._get_integer(input, IntegerType.Int24) - 1)
        elif expr_type == DecodeExpressionType.Int24:
            return nodes.StaticInteger(self._get_integer(input, IntegerType.Int24))
        elif expr_type == DecodeExpressionType.Int24_Lsh8:
            return nodes.StaticInteger(self._get_integer(input, IntegerType.Int24) << 8)
        elif expr_type == DecodeExpressionType.Int24_SafeZero:
            v16 = _read_byte(input)
            v8 = _read_byte(input)
            v0 = _read_byte(input)

            v = 0
            if v16 != 0xFF:
                v |= v16 << 16
            if v8 != 0xFF:
                v |= v8 << 8
            if v0 != 0xFF:
                v |= v0

            return nodes.StaticInteger(v)
        elif expr_type == DecodeExpressionType.Int32:
            return nodes.StaticInteger(self._get_integer(input, IntegerType.Int32))
        elif expr_type in (DecodeExpressionType.GreaterThanOrEqualTo,
                           DecodeExpressionType.GreaterThan,
                           DecodeExpressionType.LessThanOrEqualTo,
                           DecodeExpressionType.LessThan,
                           DecodeExpressionType.NotEqual,
                           DecodeExpressionType.Equal):
            left = self._decode_expression(input)
            right = self._decode_expression(input)
            return nodes.Comparison(expr_type, left, right)
        elif expr_type in (DecodeExpressionType.IntegerParameter,
                           DecodeExpressionType.PlayerParameter,
                           DecodeExpressionType.StringParameter,
                           DecodeExpressionType.ObjectParameter):
            return nodes.Parameter(expr_type, self._decode_expression(input))
        else:
            raise RuntimeError('Expression type not supported: %s' % expr_type)

    def _decode_generic_element(self, input: io.BytesIO, tag: TagType, length: int, arg_count: int, has_content: bool) -> INode:
        if length == 0:
            return nodes.EmptyElement(tag)
        arguments = []
        for _ in range(arg_count):
            arguments += [self._decode_expression(input)]

        content = None  # type: INode
        if has_content:
            content = self._decode_expression(input)

        return nodes.GenericElement(tag, content, *arguments)

    def _decode_generic_element_with_variable_arguments(self,
                                                        input: io.BytesIO,
                                                        tag: TagType,
                                                        length: int,
                                                        min_count: int,
                                                        max_count: int) -> INode:
        end = input.tell() + length
        args = []  # type: List[INode]
        i = 0
        while i < max_count and input.tell() < end:
            args.append(self._decode_expression(input))
            i += 1
        return nodes.GenericElement(tag, None, *args)

    def _decode_generic_surrounding_tag(self, input: io.BytesIO, tag: TagType, length: int) -> INode:
        if length != 1:
            raise RuntimeError('Out of range: length')
        status = self._get_integer(input)
        if status == 0:
            return nodes.CloseTag(tag)
        if status == 1:
            return nodes.OpenTag(tag, None)
        raise RuntimeError('Invalid data')

    def _decode_zero_padded_value(self, input: io.BytesIO, tag: TagType, length: int) -> INode:
        val = self._decode_expression(input)
        arg = self._decode_expression(input)
        return nodes.GenericElement(tag, val, arg)

    def _decode_color(self, input: io.BytesIO, tag: TagType, length: int) -> INode:
        t = _read_byte(input)
        if length == 1 and t == 0xEC:
            return nodes.CloseTag(tag)
        color = self._decode_expression(input, t)
        return nodes.OpenTag(tag, color)

    def _decode_ui_color(self, input: io.BytesIO, tag: TagType, length: int) -> INode:
        t = _read_byte(input)
        if length == 1 and t == 0x01:
            return nodes.CloseTag(tag)
        color = self._decode_expression(input, t)
        return nodes.OpenTag(tag, color)

    def _decode_format(self, input: io.BytesIO, tag: TagType, length: int) -> INode:
        end = input.tell() + length

        arg1 = self._decode_expression(input)
        arg2 = nodes.StaticByteArray(input.read(end - input.tell()))
        return nodes.GenericElement(tag, None, arg1, arg2)

    def _decode_if(self, input: io.BytesIO, tag: TagType, length: int) -> INode:
        end = input.tell() + length

        condition = self._decode_expression(input)
        true_value, false_value = self._decode_conditional_outputs(input, end)

        return nodes.IfElement(tag, condition, true_value, false_value)

    def _decode_if_equals(self, input: io.BytesIO, tag: TagType, length: int) -> INode:
        end = input.tell() + length

        left = self._decode_expression(input)
        right = self._decode_expression(input)
        true_value, false_value = self._decode_conditional_outputs(input, end)

        return nodes.IfEqualsElement(tag, left, right, true_value, false_value)

    def _decode_if_self(self, input: io.BytesIO, tag: TagType, length: int) -> INode:
        end = input.tell() + length

        left = self._decode_expression(input)
        true_value, false_value = self._decode_conditional_outputs(input, end)

        return nodes.IfSelfElement(tag, left, true_value, false_value)

    def _decode_conditional_outputs(self, input: io.BytesIO, end: int) -> Tuple[INode, INode]:
        true_value = None  # type: INode
        false_value = None  # type: INode
        exprs = []  # type: List[INode]
        while input.tell() != end:
            expr = self._decode_expression(input)
            exprs.append(expr)

        # Only one instance with more than two expressions (LogMessage.en[1115][4])
        # Not sure how it should be handled, discarding all but first and second for now.
        if len(exprs) > 0:
            true_value = exprs[0]
        if len(exprs) > 1:
            false_value = exprs[1]

        return true_value, false_value

    def _decode_switch(self, input: io.BytesIO, tag: TagType, length: int) -> INode:
        end = input.tell() + length
        case_switch = self._decode_expression(input)

        cases = dict()  # type: Dict[int, INode]
        i = 1
        while input.tell() < end:
            cases[i] = self._decode_expression(input)
            i += 1

        return nodes.SwitchElement(tag, case_switch, cases)

    @staticmethod
    def get_integer(input: io.BytesIO, type: IntegerType = None) -> int:
        return XivStringDecoder._get_integer(input, type)

    @staticmethod
    def _get_integer(input: io.BytesIO, type: IntegerType = None) -> int:
        BYTE_LENGTH_CUTOFF = 0xF0

        if type is None:
            type = _read_byte(input)
        if isinstance(type, IntegerType):
            t = type.value
        else:
            t = type  # type: int

        if t < BYTE_LENGTH_CUTOFF:
            return t - 1

        if t == IntegerType.Byte.value:
            return _read_byte(input)
        elif t == IntegerType.ByteTimes256.value:
            return _read_byte(input) * 256
        elif t == IntegerType.Int16.value:
            return (_read_byte(input) <<  8) | \
                   (_read_byte(input)      )
        elif t == IntegerType.Int24.value:
            return (_read_byte(input) << 16) | \
                   (_read_byte(input) <<  8) | \
                   (_read_byte(input)      )
        elif t == IntegerType.Int32.value:
            return (_read_byte(input) << 24) | \
                   (_read_byte(input) << 16) | \
                   (_read_byte(input) <<  8) | \
                   (_read_byte(input)      )
        else:
            raise RuntimeError('Type 0x%02x not supported' % type)
