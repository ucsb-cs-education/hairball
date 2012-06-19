NOT_IMPL_MSG = '{0!r} needs to implement function {1!r}'
NO_DOCSTRING = '{0!r} needs a class docstring (comment).'

class PluginBase(object):
    def __init__(self, name, batch):
        self.name = name
        self.batch = batch
        if not self.__doc__:
            raise NotImplementedError(NO_DOCSTRING.format(self.name))
        print 'Loaded {0!r}'.format(self.name)

    def process(self, scratch_file):
        raise NotImplementedError(NOT_IMPL_MSG.format(self.name, 'process'))

    def finalize(self):
        raise NotImplementedError(NOT_IMPL_MSG.format(self.name, 'finalize'))
