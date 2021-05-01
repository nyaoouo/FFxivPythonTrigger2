class AttributeExistsException(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Attribute '%s' already exists" % self.name


class AttributeNotFoundException(Exception):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "Attribute '%s' not found" % self.name


class AttrContainer(object):
    def __init__(self):
        self.attrs=dict()

    def register(self, name, obj):
        if name in self.attrs :
            raise AttributeExistsException(name)
        self.attrs[name] = obj

    def unregister(self, name):
        if name not in self.attrs:
            raise AttributeNotFoundException(name)
        del self.attrs[name]

    def __getitem__(self, name):
        if name not in self.attrs:
            raise AttributeNotFoundException(name)
        return self.attrs[name]

    def __getattr__(self,name):
        return self[name]
