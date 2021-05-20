from typing import Union, Dict, Tuple
from abc import abstractmethod
from copy import copy

from . import nodes
from .expressions import IExpression
from .parameters import ParameterBase
from .utils import DecodeExpressionType


class IEvaluationFunctionProvider(object):

    @abstractmethod
    def compare(self,
                parameters: 'EvaluationParameters',
                comparison_type: DecodeExpressionType,
                left: 'nodes.INode',
                right: 'nodes.INode') -> bool:
        pass

    @abstractmethod
    def evaluate_generic_element(self,
                                 parameters: 'EvaluationParameters',
                                 element: 'nodes.GenericElement') -> IExpression:
        pass

    @abstractmethod
    def to_boolean(self, value: IExpression) -> bool: pass

    @abstractmethod
    def try_convert_to_integer(self, value: IExpression) -> Union[int, type(None)]: pass

    @abstractmethod
    def to_integer(self, value: IExpression) -> int: pass


class EvaluationParameters(object):
    @property
    def fallback_value(self) -> object:
        return self.__fallback_value

    @fallback_value.setter
    def fallback_value(self, value):
        self.__fallback_value = value

    @property
    def function_provider(self) -> IEvaluationFunctionProvider:
        return self.__function_provider

    @property
    def top_level_parameters(self) -> ParameterBase:
        return self.__top_level_parameters

    def __init__(self, function_provider: IEvaluationFunctionProvider = None,
                 is_copy: bool = False):
        if is_copy:
            return
        if function_provider is None:
            raise ValueError
        self.__fallback_value = None  # type: object
        self.__parameters = {}  # type: Dict[DecodeExpressionType, ParameterBase]
        self.__top_level_parameters = ParameterBase()
        self.__function_provider = function_provider

    def __copy__(self):
        clone = EvaluationParameters(is_copy=True)
        clone.__function_provider = self.function_provider
        clone.__top_level_parameters = copy(self.top_level_parameters)
        return clone

    def __getitem__(self, item: Tuple[DecodeExpressionType, int]) -> object:
        if item[0] not in self.__parameters:
            return self.fallback_value
        pb = self.__parameters[item[0]]
        return pb[item[1]]

    def __setitem__(self, key: Tuple[DecodeExpressionType, int], value: object):
        pb = self.__parameters.get(key[0], None)
        if pb is None:
            raise NotImplementedError
        pb[key[1]] = value
