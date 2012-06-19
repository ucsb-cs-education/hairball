from hashlib import sha1
from random import random

NOT_IMPL_MSG = '{0!r} needs to implement function {1!r}'
NO_DOCSTRING = '{0!r} needs a class docstring (comment).'

HTML_TMPL = """<div class="plugin_title" id="{key}">{name}</div>
<div class="hidden" id="{key}_body">{body}</div>"""

class PluginBase(object):
    def __init__(self, name, batch):
        self.name = name
        self.batch = batch
        if not self.__doc__:
            raise NotImplementedError(NO_DOCSTRING.format(self.name))
        print 'Loaded {0!r}'.format(self.name)

    def html_wrap(self, body):
        key = sha1(str(random())).hexdigest()
        return HTML_TMPL.format(key=key, name=self.name, body=body)

    def process(self, scratch):
        return self.html_wrap(self._process(scratch))

    def finalize(self):
        raise NotImplementedError(NOT_IMPL_MSG.format(self.name, 'finalize'))
