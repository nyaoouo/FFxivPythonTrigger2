import yaml
import yaml.constructor
from typing import TypeVar, Generic, Type

T = TypeVar('T', bound=yaml.YAMLObject)


class ObjectYamlLoader(yaml.SafeLoader, Generic[T]):

    def __init__(self, *args, **kwargs):
        super(ObjectYamlLoader, self).__init__(*args, **kwargs)
        self.cls = kwargs['cls'] or None  # type: Type[T]
        self.add_path_resolver(self.cls.yaml_tag, [], dict)
