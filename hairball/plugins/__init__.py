import kurt
from functools import wraps
from hashlib import sha1
from random import random

NOT_IMPL_MSG = '{0!r} needs to implement function {1!r}'
NO_DOCSTRING = '{0!r} needs a class docstring (comment).'

HTML_TMPL = """<div class="header" id="{key}">{name}</div>
<div class="description">{description}</div>
<div class="hidden" id="{key}_body">{body}</div>"""

class PluginController(object):
    """The simple plugin name should go on the first comment line.

    The plugin description should start on the third line and can span as many
    lines as needed, though all newlines will be treated as a single space.

    If you are seeing this message it means you need to define a docstring for
    your plugin.
    """

    @staticmethod
    def save_png(image, image_name, sprite_name=''):
        """Save the image to disc and returns the relative path to the file.

        Use the companion function `get_image_html` in the view to get an html
        view for the image."""
        path = '{0}{1}.png'.format(sprite_name, image_name).replace('/', '_')
        image.save_png(path)
        return path

    @property
    def description(self):
        lines = []
        for line in self.__doc__.split('\n')[2:]:
            line = line.strip()
            if line:
                lines.append(line)
        return ' '.join(lines)

    @property
    def name(self):
        return self.__doc__.split('\n')[0]

    def _process(self, scratch, thumbnail_path=None, **kwargs):
        # We need to save the thumbnail somewhere; might as well do it here
        self.save_png(scratch.info['thumbnail'], 'thumbnail')

        # also save a copy of the thumbnail in the backup directory
        if thumbnail_path:
            self.save_png_dir(scratch.info['thumbnail'], thumbnail_path)

        return self.analyze(scratch, **kwargs)

    def view_data(self, **kwargs):
        kwargs['_name'] = self.name
        kwargs['_description'] = self.description
        return kwargs


class PluginView(object):
    IMG_TMPL = '<img class="scratch-image" src="{0}" />\n<br />\n'

    @staticmethod
    def get_image_html(relative_path):
        return PluginView.IMG_TMPL.format(relative_path)

    def __init__(self, function):
        wraps(function)(self)
        self.function = function

    def __call__(self, *args, **kwargs):
        data = self.function(*args, **kwargs)
        body = self.view(data)
        key = sha1(str(random())).hexdigest()
        return HTML_TMPL.format(key=key, name=data['_name'], body=body,
                                description=data['_description'])

    def __get__(self, instance, instance_type):
        return self.__class__(self.function.__get__(instance, instance_type))


class PluginWrapper(object):
    def __init__(self, html=None, txt=None):
        self.html = html
        self.txt = txt

    def __call__(self, function):
        html_decorator = txt_decorator = None
        if self.html:
            html_decorator = self.html(function)
        if self.txt:
            txt_decorator = self.txt(function)
        def wrapped(*args, **kwargs):
            if '_decorator' not in kwargs:
                return function(*args, **kwargs)
            selection = kwargs['_decorator']
            del kwargs['_decorator']

            if html_decorator and selection == 'html':
                return html_decorator(*args, **kwargs)
            elif txt_decorator and selection == 'txt':
                return txt_decorator(*args, **kwargs)
            else:
                raise Exception('Unknown decorator type {0!r}'
                                .format(selection))
        return wrapped


### Delete everything below here once it has been moved to the new system


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
            if isinstance(block, kurt.scripts.Block):
                for b in PluginController.get_block(block, level):
                    yield b

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
            yield (block.name, level, block)
            for arg in block.args:
                if hasattr(arg, '__iter__'):
                    for b in PluginController.block_iter(arg, level + 1):
                        yield b
                elif isinstance(arg, kurt.scripts.Block):
                    for b in PluginController.get_block(arg, level):
                        yield b

    #only works if there aren't multiple green flag scripts
    @staticmethod
    def pull_green_flag(scripts):
        greenflag = []
        other = scripts
        for script in scripts:
            if PluginController.starts_green_flag(script):
                greenflag.append(script)
                other.remove(script)
        return (greenflag, other)

    @staticmethod
    def save_png(image, image_name, sprite_name=''):
        """Save the image to disc and returns the relative path to the file.

        Use the companion function `get_image_html` in the view to get an html
        view for the image."""
        path = '{0}{1}.png'.format(sprite_name, image_name).replace('/', '_')
        image.save_png(path)
        return path

    @staticmethod
    def save_png_dir(image, image_absolute_path_name):
        """Save the image to disc and returns the absolute path to the file.
        """

        image.save_png(image_absolute_path_name)
        return image_absolute_path_name

    @staticmethod
    def script_iter(scriptlist, dead=False):
        acceptable = ["KeyEventHatMorph", "MouseClickEventHatMorph"]
        for script in scriptlist:
            first = script.blocks[0]
            if dead:
                if first.name != "EventHatMorph":
                    if first.name not in acceptable:
                        yield script
                elif first.args[0] == "":
                    yield script
            else:
                if first.name in acceptable:
                    yield script
                elif first.name == "EventHatMorph" and first.args[0] != "":
                    yield script

    @staticmethod
    def starts_green_flag(script):
        if script.blocks[0].name == 'EventHatMorph':
            if script.blocks[0].args[0] == 'Scratch-StartClicked':
                return True
        else:
            return False

    @property
    def description(self):
        lines = []
        for line in self.__doc__.split('\n')[2:]:
            line = line.strip()
            if line:
                lines.append(line)
        return ' '.join(lines)

    @property
    def name(self):
        return self.__doc__.split('\n')[0]

    def _process(self, scratch):
        # We need to save the thumbnail somewhere; might as well do it here
        self.thumbnail = self.save_png(scratch.info['thumbnail'], 'thumbnail')
        return self.analyze(scratch)

    def view_data(self, **kwargs):
        kwargs['_name'] = self.name
        kwargs['_description'] = self.description
        kwargs['_thumbnail'] = self.thumbnail
        return kwargs

class PluginView(object):
    IMG_TMPL = '<img class="scratch-image" src="{0}" />\n<br />\n'
    SUBHEADING = '<div class="subheading">{0}</div>'

    @staticmethod
    def get_image_html(relative_path):
        return PluginView.IMG_TMPL.format(relative_path)

    @staticmethod
    def to_scratch_blocks(heading, scripts):
        """Output the scripts in an html-ready scratch blocks format."""
        data = []
        for script in scripts:
            data.append('<div class="float scratchblocks">{0}</div>'
                        .format(script.to_block_plugin()))
        heading = PluginView.SUBHEADING.format(heading)
        return ('<div>\n{0}\n<div>{1}</div>\n<div class="clear"></div>\n'
                '</div>\n').format(heading, ''.join(data))

    def __init__(self, function):
        wraps(function)(self)
        self.function = function

    def __call__(self, *args, **kwargs):
        data = self.function(*args, **kwargs)
        body = self.view(data)
        key = sha1(str(random())).hexdigest()
        return HTML_TMPL.format(key=key, name=data['_name'], body=body,
                                description=data['_description'])

    def __get__(self, instance, instance_type):
        return self.__class__(self.function.__get__(instance, instance_type))
