from hashlib import sha1
from random import random

NOT_IMPL_MSG = '{0!r} needs to implement function {1!r}'
NO_DOCSTRING = '{0!r} needs a class docstring (comment).'

HTML_TMPL = """<div class="heading" id="{key}">{name}</div>
<div class="hidden" id="{key}_body">{body}</div>"""


class PluginBase(object):
    SUBHEADING = '<div class="subheading">{0}</div>'

    @staticmethod
    def to_scratch_blocks(heading, scripts):
        """Output the scripts in an html-ready scratch blocks format."""
        data = []
        for script in scripts:
            data.append('<div class="float scratchblocks">{0}</div>'
                        .format(script.to_block_plugin()))
        heading = PluginBase.SUBHEADING.format(heading)
        return ('{0}\n<div class="clear"></div>\n'
                '<div>{1}</div>').format(heading, ''.join(data))

    def __init__(self, name, batch):
        self.name = name
        self.batch = batch
        if not self.__doc__:
            raise NotImplementedError(NO_DOCSTRING.format(self.name))
        print 'Loaded {0!r}'.format(self.name)

    def finalize(self):
        raise NotImplementedError(NOT_IMPL_MSG.format(self.name, 'finalize'))

    def html_wrap(self, body):
        key = sha1(str(random())).hexdigest()
        return HTML_TMPL.format(key=key, name=self.name, body=body)

    def process(self, scratch):
        return self.html_wrap(self._process(scratch))
