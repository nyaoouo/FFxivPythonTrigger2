from enum import Enum


class DecodeExpressionType(Enum):
    GreaterThanOrEqualTo = 0xE0  # Followed by two variables
    GreaterThan = 0xE1  # Followed by one variable
    LessThanOrEqualTo = 0xE2
    LessThan = 0xE3
    Equal = 0xE4
    NotEqual = 0xE5

    IntegerParameter = 0xE8
    PlayerParameter = 0xE9
    StringParameter = 0xEA
    ObjectParameter = 0xEB

    Byte = 0xF0
    Int16_MinusOne = 0xF1
    Int16_1 = 0xF2
    Int16_2 = 0xF4
    Int24_MinusOne = 0xF5
    Int24 = 0xF6

    Int24_SafeZero = 0xFA
    Int24_Lsh8 = 0xFD
    Int32 = 0xFE

    Decode = 0xFF


class IntegerType(Enum):
    Byte = 0xF0
    ByteTimes256 = 0xF1
    Int16 = 0xF2
    Int24 = 0xFA
    Int32 = 0xFE


class NodeFlags(Enum):
    none = 0x00
    HasArguments = 0x01
    HasChildren = 0x02
    IsExpression = 0x04
    IsConditional = 0x08
    IsStatic = 0x10


class StringTokens(object):
    TAG_OPEN = '<'
    TAG_CLOSE = '>'
    ELEMENT_CLOSE = '/'
    ARGUMENTS_OPEN = '('
    ARGUMENTS_CLOSE = ')'
    ARGUMENTS_SEPARATOR = ','

    ELSE_TAG = TAG_OPEN + 'Else' + ELEMENT_CLOSE + TAG_CLOSE
    CASE_TAG_NAME = 'Case'

    INVERT_NAME = 'Not'

    TOP_LEVEL_PARAMETER_NAME = 'TopLevelParameter'


class TagType(Enum):
    none = 0x00
    ResetTime = 0x06
    Time = 0x07  # TODO: It seems to set the time used further on.
    If = 0x08
    Switch = 0x09
    Name = 0x0A  # Used in wedding and PvP messages. Returns the character's full name.
    IfEquals = 0x0C  # (left, right, true[, false)
    IfSelf = 0x0F  # Added in 2020.02.11.0000.0000: Similar but omits right
    #                IfSelf == IfEquals(<left>, ObjectParameter(1), true[, false])
    LineBreak = 0x10
    Gui = 0x12
    Color = 0x13
    Color2 = 0x14
    SoftHyphen = 0x16
    Unknown17 = 0x17
    Emphasis2 = 0x19
    Emphasis = 0x1A
    Unknown1B = 0x1B  # TODO: QuickChatTransient
    Unknown1C = 0x1C  # TODO: QuickChatTransient
    Indent = 0x1D
    CommandIcon = 0x1E
    Dash = 0x1F
    Value = 0x20
    Format = 0x22
    TwoDigitValue = 0x24
    DecimalValue = 0x26
    Sheet = 0x28
    Highlight = 0x29
    Clickable = 0x2B
    Split = 0x2C
    Unknown2D = 0x2D
    Fixed = 0x2E
    Unknown2F = 0x2F
    SheetJa = 0x30
    SheetEn = 0x31
    SheetDe = 0x32
    SheetFr = 0x33
    InstanceContent = 0x40
    UIForeground = 0x48  # Lookup into UIColor[n]/UIForeground
    UIGlow = 0x49  # Lookup into UIColor[n]/UIGlow
    ZeroPaddedValue = 0x50
    OrdinalNumber = 0x51
    Sfx = 0x60  # Usually for log messages, causes SE[n] to play when printed
