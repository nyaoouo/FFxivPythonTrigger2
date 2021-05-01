from typing import TypeVar, Generic, Type, Union, Iterable, List, Dict
from abc import ABC, abstractmethod

from ..utils import TagType, NodeFlags, StringTokens, DecodeExpressionType
from .. import expressions
from .. import evaluation

T = TypeVar('T')


class INodeVisitor(Generic[T]):
    @abstractmethod
    def visit(self, node: Union['XivString', 'OpenTag', 'CloseTag', 'IfElement', 'GenericElement',
                                'EmptyElement', 'DefaultElement', 'Comparison', 'TopLevelParameter',
                                'SwitchElement', 'StaticString', 'StaticInteger', 'StaticByteArray',
                                'Parameter']) -> T:
        pass


class INode(ABC):
    @property
    @abstractmethod
    def tag(self) -> TagType: pass

    @property
    @abstractmethod
    def flags(self) -> NodeFlags: pass

    @abstractmethod
    def __str__(self): pass

    @abstractmethod
    def accept(self, visitor: INodeVisitor[T]) -> T: pass


class IExpressionNode(INode):
    @abstractmethod
    def evaluate(self, parameters: 'evaluation.EvaluationParameters') -> expressions.IExpression:
        pass


class IConditionalNode(IExpressionNode):
    @property
    @abstractmethod
    def condition(self) -> INode: pass

    @property
    @abstractmethod
    def true_value(self) -> INode: pass

    @property
    @abstractmethod
    def false_value(self) -> INode: pass


class INodeWithArguments(INode):
    @property
    @abstractmethod
    def arguments(self) -> Iterable[INode]: pass


class INodeWithChildren(INode):
    @property
    @abstractmethod
    def children(self) -> Iterable[INode]: pass


class IStaticNode(INode):
    @property
    @abstractmethod
    def value(self) -> object: pass


class ArgumentCollection(Iterable[INode]):
    @property
    def has_items(self): return len(self.__items) > 0

    def __iter__(self):
        return iter(self.__items)

    def __init__(self, *items: INode):
        self.__items = list(items)

    def __str__(self):
        s = ''
        if self.has_items:
            s += StringTokens.ARGUMENTS_OPEN
            s += StringTokens.ARGUMENTS_SEPARATOR.join(map(str, self))
            s += StringTokens.ARGUMENTS_CLOSE
        return s


class CloseTag(IExpressionNode):
    @property
    def tag(self): return self.__tag

    @property
    def flags(self): return NodeFlags.IsExpression | NodeFlags.IsStatic

    def __init__(self, tag: TagType):
        self.__tag = tag

    def __str__(self):
        return "%s%s%s%s" % (StringTokens.TAG_OPEN,
                             StringTokens.ELEMENT_CLOSE,
                             self.tag.name,
                             StringTokens.TAG_CLOSE)

    def accept(self, visitor: INodeVisitor[T]):
        return visitor.visit(self)

    def evaluate(self, parameters: 'evaluation.EvaluationParameters'):
        return expressions.CloseTag(self.tag)


class Comparison(IExpressionNode):
    @property
    def tag(self): return TagType.none

    @property
    def flags(self): return NodeFlags.IsExpression

    @property
    def left(self) -> INode: return self.__left

    @property
    def comparison_type(self) -> DecodeExpressionType: return self.__comparison_type

    @property
    def right(self) -> INode: return self.__right

    def __init__(self, comparison_type: DecodeExpressionType, left: INode, right: INode):
        self.__comparison_type = comparison_type
        self.__left = left
        self.__right = right

    def __str__(self):
        s = ''
        s += self.comparison_type.name
        s += StringTokens.ARGUMENTS_OPEN
        if self.left is not None:
            s += str(self.left)
        if self.right is not None:
            s += StringTokens.ARGUMENTS_SEPARATOR
            s += str(self.right)
        s += StringTokens.ARGUMENTS_CLOSE
        return s

    def accept(self, visitor: INodeVisitor[T]) -> T:
        return visitor.visit(self)

    def evaluate(self, parameters: 'evaluation.EvaluationParameters') -> expressions.IExpression:
        return expressions.GenericExpression(
            parameters.function_provider.compare(parameters,
                                                 self.comparison_type,
                                                 self.left,
                                                 self.right))


class DefaultElement(INode):
    @property
    def tag(self): return self.__tag

    @property
    def data(self) -> INode: return self.__data

    @property
    def flags(self): return NodeFlags.IsStatic

    def __init__(self, tag: TagType, inner_buffer: bytes):
        self.__tag = tag
        self.__data = StaticByteArray(inner_buffer)

    def __str__(self):
        s = ''
        s += StringTokens.TAG_OPEN
        s += self.tag.name
        if len(self.__data.value) == 0:
            s += StringTokens.ELEMENT_CLOSE
            s += StringTokens.TAG_CLOSE
        else:
            s += StringTokens.TAG_CLOSE
            s += str(self.__data)
            s += StringTokens.TAG_OPEN
            s += StringTokens.ELEMENT_CLOSE
            s += self.tag.name
            s += StringTokens.TAG_CLOSE
        return s

    def accept(self, visitor: INodeVisitor[T]):
        return visitor.visit(self)


class EmptyElement(INode):
    @property
    def tag(self): return self.__tag

    @property
    def flags(self): return NodeFlags.IsStatic

    def __init__(self, tag: TagType):
        self.__tag = tag

    def __str__(self):
        return "%s%s%s%s" % (StringTokens.TAG_OPEN,
                             self.tag.name,
                             StringTokens.ELEMENT_CLOSE,
                             StringTokens.TAG_CLOSE)

    def accept(self, visitor: INodeVisitor[T]):
        return visitor.visit(self)


class GenericElement(INodeWithChildren, INodeWithArguments, IExpressionNode):
    @property
    def tag(self): return self.__tag

    @property
    def arguments(self): return self.__arguments

    @property
    def content(self) -> INode: return self.__content

    @property
    def flags(self):
        f = NodeFlags.IsExpression
        if self.__arguments.has_items:
            f |= NodeFlags.HasArguments
        if self.content is not None:
            f |= NodeFlags.HasChildren
        return f

    def __init__(self, tag: TagType, content: INode, *arguments: INode):
        self.__tag = tag
        self.__arguments = ArgumentCollection(*arguments)
        self.__content = content

    def __str__(self):
        s = ''
        s += StringTokens.TAG_OPEN
        s += self.tag.name
        s += str(self.__arguments)

        if self.content is None:
            s += StringTokens.ELEMENT_CLOSE
            s += StringTokens.TAG_CLOSE
        else:
            s += StringTokens.TAG_CLOSE
            s += str(self.content)
            s += StringTokens.TAG_OPEN
            s += StringTokens.ELEMENT_CLOSE
            s += self.tag.name
            s += StringTokens.TAG_CLOSE
        return s

    def accept(self, visitor: INodeVisitor[T]):
        return visitor.visit(self)

    @property
    def children(self):
        yield self.content

    def evaluate(self, parameters: 'evaluation.EvaluationParameters'):
        return parameters.function_provider.evaluate_generic_element(parameters, self)


class IfElement(IConditionalNode):
    @property
    def tag(self): return self.__tag

    @property
    def flags(self): return NodeFlags.IsExpression | NodeFlags.IsConditional

    @property
    def condition(self): return self.__condition

    @property
    def true_value(self): return self.__true_value

    @property
    def false_value(self): return self.__false_value

    def __init__(self, tag: TagType, condition: INode, true_value: INode, false_value: INode):
        if condition is None:
            raise ValueError('condition')
        self.__tag = tag
        self.__condition = condition
        self.__true_value = true_value
        self.__false_value = false_value

    def __str__(self):
        s = StringTokens.TAG_OPEN
        s += self.tag.name
        s += StringTokens.ARGUMENTS_OPEN
        s += str(self.condition)
        s += StringTokens.ARGUMENTS_CLOSE
        s += StringTokens.TAG_CLOSE

        if self.true_value is not None:
            s += str(self.true_value)

        if self.false_value is not None:
            s += StringTokens.ELSE_TAG
            s += str(self.false_value)

        s += StringTokens.TAG_OPEN
        s += StringTokens.ELEMENT_CLOSE
        s += self.tag.name
        s += StringTokens.TAG_CLOSE
        return s

    def accept(self, visitor: INodeVisitor[T]):
        return visitor.visit(self)

    def evaluate(self, parameters: 'evaluation.EvaluationParameters'):
        eval_cond = self.condition.evaluate(parameters)
        if parameters.function_provider.to_boolean(eval_cond):
            return self.true_value.evaluate(parameters)
        return self.false_value.evaluate(parameters)


class IfEqualsElement(IfElement):
    def __init__(self, tag: TagType, left_value: INode, right_value: INode, true_value: INode, false_value: INode):
        super(IfEqualsElement, self).__init__(tag,
                                              Comparison(DecodeExpressionType.Equal, left_value, right_value),
                                              true_value, right_value)


class IfSelfElement(IfElement):
    def __init__(self, tag: TagType, left_value: INode, true_value: INode, false_value: INode):
        super(IfSelfElement, self).__init__(tag,
                                            Comparison(DecodeExpressionType.Equal, left_value, None),
                                            true_value, false_value)

    def evaluate(self, parameters: 'evaluation.EvaluationParameters'):
        # Condition is a little wonky in order to format string correctly.
        condition = Comparison(DecodeExpressionType.Equal,
                               self.condition.left,
                               Parameter(DecodeExpressionType.ObjectParameter, StaticInteger(1)))
        eval_cond = condition.evaluate(parameters)
        if parameters.function_provider.to_boolean(eval_cond):
            return self.true_value.evaluate(parameters)
        return self.false_value.evaluate(parameters)


class OpenTag(IExpressionNode):
    @property
    def tag(self): return self.__tag

    @property
    def flags(self): return NodeFlags.IsExpression

    @property
    def arguments(self): return self.__arguments

    def __init__(self, tag: TagType, *arguments: INode):
        self.__tag = tag
        self.__arguments = ArgumentCollection(*arguments)

    def __str__(self):
        s = StringTokens.TAG_OPEN
        s += self.tag.name
        s += str(self.__arguments)
        s += StringTokens.TAG_CLOSE
        return s

    def accept(self, visitor: INodeVisitor[T]):
        return visitor.visit(self)

    def evaluate(self, parameters: 'evaluation.EvaluationParameters'):
        return expressions.OpenTag(self.tag, [arg.evaluate(parameters) for arg in self.arguments])


class Parameter(IExpressionNode):
    @property
    def tag(self) -> TagType: return TagType.none

    @property
    def flags(self) -> NodeFlags: return NodeFlags.IsExpression

    @property
    def parameter_type(self) -> DecodeExpressionType: return self.__parameter_type

    @property
    def parameter_index(self) -> INode: return self.__parameter_index

    def __init__(self, parameter_type: DecodeExpressionType, parameter_index: INode):
        if parameter_type is None:
            raise ValueError
        self.__parameter_type = parameter_type
        self.__parameter_index = parameter_index

    def __str__(self):
        s = ''
        s += self.parameter_type.name
        s += StringTokens.ARGUMENTS_OPEN
        s += str(self.parameter_index)
        s += StringTokens.ARGUMENTS_CLOSE
        return s

    def accept(self, visitor: INodeVisitor[T]) -> T:
        return visitor.visit(self)

    def evaluate(self, parameters: 'evaluation.EvaluationParameters') -> expressions.IExpression:
        eval_index = self.parameter_index.evaluate(parameters)
        index = parameters.function_provider.to_integer(eval_index)
        return expressions.GenericExpression(parameters[(self.parameter_type, index)])


class StaticByteArray(IStaticNode):
    @property
    def tag(self): return TagType.none

    @property
    def flags(self): return NodeFlags.IsStatic

    @property
    def value(self) -> bytes: return self.__value

    def __init__(self, value: bytes):
        self.__value = value

    def __str__(self):
        return self.value.hex().upper()

    def accept(self, visitor: INodeVisitor[T]):
        return visitor.visit(self)


class StaticInteger(IStaticNode):
    @property
    def tag(self): return TagType.none

    @property
    def flags(self): return NodeFlags.IsStatic

    @property
    def value(self) -> int: return self.__value

    def __init__(self, value: int):
        self.__value = value

    def __str__(self):
        return str(self.value)

    def accept(self, visitor: INodeVisitor[T]):
        return visitor.visit(self)


class StaticString(IStaticNode):
    @property
    def tag(self): return TagType.none

    @property
    def flags(self): return NodeFlags.IsStatic

    @property
    def value(self) -> str: return self.__value

    def __init__(self, value: str):
        self.__value = value

    def __str__(self):
        return str(self.value)

    def accept(self, visitor: INodeVisitor[T]):
        return visitor.visit(self)


class SwitchElement(IExpressionNode):
    @property
    def tag(self) -> TagType: return self.__tag

    @property
    def flags(self) -> NodeFlags: return NodeFlags.IsExpression

    @property
    def case_switch(self) -> INode: return self.__case_switch

    @property
    def cases(self) -> Dict[int, INode]: return self.__cases

    def __init__(self, tag: TagType, case_switch: INode, cases: Dict[int, INode]):
        if case_switch is None:
            raise ValueError('case_switch')
        if cases is None:
            raise ValueError('cases')
        self.__tag = tag
        self.__case_switch = case_switch
        self.__cases = dict(cases)

    def __str__(self):
        s = ''
        s += StringTokens.TAG_OPEN
        s += self.tag.name
        s += StringTokens.ARGUMENTS_OPEN
        s += str(self.case_switch)
        s += StringTokens.ARGUMENTS_CLOSE
        s += StringTokens.TAG_CLOSE

        for key, value in self.cases.items():
            s += StringTokens.TAG_OPEN
            s += StringTokens.CASE_TAG_NAME
            s += StringTokens.ARGUMENTS_OPEN
            s += str(key)
            s += StringTokens.ARGUMENTS_CLOSE
            s += StringTokens.TAG_CLOSE

            s += str(value)

            s += StringTokens.TAG_OPEN
            s += StringTokens.ELEMENT_CLOSE
            s += StringTokens.CASE_TAG_NAME
            s += StringTokens.TAG_CLOSE

        s += StringTokens.TAG_OPEN
        s += StringTokens.ELEMENT_CLOSE
        s += self.tag.name
        s += StringTokens.TAG_CLOSE
        return s

    def accept(self, visitor: INodeVisitor[T]) -> T:
        return visitor.visit(self)

    def evaluate(self, parameters: 'evaluation.EvaluationParameters') -> expressions.IExpression:
        eval_switch = self.case_switch.evaluate(parameters)
        as_int = parameters.function_provider.to_integer(eval_switch)

        case_node = self.__cases[as_int]
        return case_node.evaluate(parameters)


class TopLevelParameter(IExpressionNode):
    @property
    def tag(self): return TagType.none

    @property
    def flags(self): return NodeFlags.IsExpression

    @property
    def value(self) -> int: return self.__value

    def __init__(self, value: int):
        self.__value = value

    def __str__(self):
        return "%s%s%s%s" % (StringTokens.TOP_LEVEL_PARAMETER_NAME,
                             StringTokens.ARGUMENTS_OPEN,
                             str(self.value),
                             StringTokens.ARGUMENTS_CLOSE)

    def accept(self, visitor: INodeVisitor[T]):
        return visitor.visit(self)

    def evaluate(self, parameters: 'evaluation.EvaluationParameters'):
        return expressions.GenericExpression(parameters.top_level_parameters[self.value])
