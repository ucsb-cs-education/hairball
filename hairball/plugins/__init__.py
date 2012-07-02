import kurt
from hashlib import sha1
from random import random

NOT_IMPL_MSG = '{0!r} needs to implement function {1!r}'
NO_DOCSTRING = '{0!r} needs a class docstring (comment).'

HTML_TMPL = """<div class="header" id="{key}">{name}</div>
<div class="description">{description}</div>
<div class="hidden" id="{key}_body">{body}</div>"""


class PluginBase(object):
    SUBHEADING = '<div class="subheading">{0}</div>'
    BLOCKMAPPING = {"position": set([("forward:", "relative"),
                                     ("gotoX:y:", "absolute"),
                                     ("gotoSpriteOrMouse:", "relative"),
                                     ("glideSecs:toX:y:elapsed:from:",
                                      "relative"),
                                     ("changeXposBy:", "relative"),
                                     ("xpos:", "absolute"),
                                     ("changeYposBy:", "relative"),
                                     ("ypos:", "absolute")]),
                    "orientation": set([("turnRight:", "relative"),
                                        ("turnLeft:", "relative"),
                                        ("heading:", "absolute"),
                                        ("pointTowards:", "relative")]),
                    "costume": set([("showBackground:", "absolute"),
                                    ("nextBackground", "relative"),
                                    ("lookLike:", "absolute"),
                                    ("nextCostume", "relative")]),
                    "volume": set([("changeVolumeBy:", "relative"),
                                   ("setVolumeTo:", "absolute")]),
                    "tempo": set([("changeTempoBy:", "relative"),
                                  ("setTempoTo:", "absolute")]),
                    "size": set([("changeSizeBy:", "relative"),
                                 ("setSizeTo:", "absolute")])}

    @staticmethod
    def block_iter(block_list, level=0):
        for block in block_list:
            for b in PluginBase.get_block(block, level):
                yield b

    @staticmethod
    def starts_green_flag(script):
        if script.blocks[0].name == 'EventHatMorph':
            if script.blocks[0].args[0] == 'Scratch-StartClicked':
                return True
        else:
            return False

    @staticmethod
    def get_block(block, level):
        # differentiate between different blocks with the same name
        if block.name == 'EventHatMorph':
            if block.args[0] == 'Scratch-StartClicked':
                yield('When green flag clicked', 0, block)
            else:
                yield('When I receive', 0, block)
        elif block.name == 'changeVariable':
            if 'setVar' in str(block.args[1]):
                yield('setVariable', level, block)
            else:
                yield('changeVariable', level, block)
        else:
            #if this is a distinct block, use the original name
            # TO DO: map names to more readable versions
            yield (block.name, level, block)
        for arg in block.args:
            if hasattr(arg, '__iter__'):
                for b in PluginBase.block_iter(arg, level + 1):
                    yield b
            elif isinstance(arg, kurt.scripts.Block):
                for b in PluginBase.get_block(arg, level):
                    yield b

    @staticmethod
    def script_iter(scriptlist, dead):
        acceptable = ["KeyEventHatMorph", "EventHatMorph",
                      "MouseClickEventHatMorph"]
        for script in scriptlist:
            if dead and script[0].name not in acceptable:
                yield script
            elif not dead and script[0].name in acceptable:
                yield script

    @staticmethod
    def save_png(image, image_name, sprite_name=''):
        name = '{0}{1}.png'.format(sprite_name, image_name).replace('/', '_')
        image.save_png(name)
        return '<img class="scratch-image" src="{0}" />\n<br />\n'.format(name)

    @staticmethod
    def to_scratch_blocks(heading, scripts):
        """Output the scripts in an html-ready scratch blocks format."""
        data = []
        for script in scripts:
            data.append('<div class="float scratchblocks">{0}</div>'
                        .format(script.to_block_plugin()))
        heading = PluginBase.SUBHEADING.format(heading)
        return ('<div>\n{0}\n<div>{1}</div>\n<div class="clear"></div>\n'
                '</div>\n').format(heading, ''.join(data))

    def __init__(self, name, batch):
        self.name = name
        self.batch = batch
        self.thumbnail = None
        if not self.__doc__:
            raise NotImplementedError(NO_DOCSTRING.format(self.name))
        print 'Loaded {0!r}'.format(self.name)

    def finalize(self):
        raise NotImplementedError(NOT_IMPL_MSG.format(self.name, 'finalize'))

    def html_wrap(self, body):
        key = sha1(str(random())).hexdigest()
        return HTML_TMPL.format(key=key, name=self.name, body=body,
                                description=self.__doc__)

    def process(self, scratch):
        self.thumbnail = self.save_png(scratch.info['thumbnail'], 'thumbnail')
        return self.html_wrap(self._process(scratch))
