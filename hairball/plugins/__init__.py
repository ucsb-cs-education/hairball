import kurt
import os
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

    def finalize(self):
        print "finalize not implemented"

    def _process(self, scratch, thumbnail_path=None, **kwargs):
        # We need to save the thumbnail somewhere; might as well do it here
        if not hasattr(scratch, 'thumbnail_saved'):
            self.save_png(scratch.info['thumbnail'], 'thumbnail')
            # also save a copy of the thumbnail in the backup directory
            if thumbnail_path:
                self.save_png_dir(scratch.info['thumbnail'], thumbnail_path)
            scratch.thumbnail_saved = True
        if not hasattr(scratch, 'plugin_prepared'):
            self.prepare_plugin(scratch)
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
    def check_empty(block):
        arithmetic = set(['+', '-', '*', '/', '<', '=', '>', '\\', 'rounded'])
        logic = set(['&', '`', 'not', 'doIf', 'doIfElse',
                     'doForeverIf', 'doWaitUntil', 'doUntil'])
        objects = set(['gotoSpriteOrMouse:', 'touching:', 'distanceTo:'])
        strings = set(['think:duration:elapsed:from:', 'think:', 'say:',
                       'say:duration:elapsed:from:', 'doAsk',
                       'concatenate:with:', 'stringLength:',
                       'broadcast:', 'doBroadcastAndWait', 'When I receive'])
        block.empty = False
        if block.name == 'letter:of:':
            if '0' in block.args or '' in block.args:
                block.empty = True
        elif block.name in arithmetic:
            if block.name == 'rounded':
                if block.args == [0]:
                    block.empty = True
            elif block.args == [0, 0]:
                block.empty = True
        elif block.name in logic:
            if block.name == '&' or block.name == '`':
                if block.args == [False, False]:
                    block.empty = True
            elif False in block.args:
                block.empty = True
        elif block.name in objects:
            if None in block.args:
                block.empty = True
        elif block.name in strings:
            if "" in block.args:
                block.empty = True
        for arg in block.args:
            if isinstance(arg, kurt.scripts.Block):
                PluginController.check_empty(arg)
                block.empty = arg.empty

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
        # skip comments
        elif block.name != "":
            #if this is a distinct block, use the original name
            yield (block.name, level, block)
            for arg in block.args:
                if hasattr(arg, '__iter__'):
                    for b in PluginController.block_iter(arg, level + 1):
                        yield b
                elif isinstance(arg, kurt.scripts.Block):
                    for b in PluginController.get_block(arg, level):
                        yield b

    @staticmethod
    def get_messages(block_list):
        for block in block_list:
            if isinstance(block, kurt.scripts.Block) and block.name != '':
                for name, level, block in PluginController.get_block(block, 0):
                    if name == "broadcast:" or name == "doBroadcastAndWait":
                        # check here if it's static or dynamic
                        if isinstance(block.args[0], kurt.scripts.Block):
                            yield "dynamic"
                        else:
                            yield block.args[0]

    @staticmethod
    def hat_type(script):
        if script.blocks[0].name == 'EventHatMorph':
            if script.blocks[0].args[0] == 'Scratch-StartClicked':
                return "When green flag clicked"
            else:
                return "When I receive"
        elif 'EventHatMorph' in script.blocks[0].name:
            return script.blocks[0].name
        else:
            return "No Hat"

    @staticmethod
    def mark_useless(blocklist):
        for block in blocklist:
            PluginController.check_empty(block)
            if not block.empty:
                for arg in block.args:
                    # lists of blocks are the stuff inside of c blocks
                    if hasattr(arg, '__iter__'):
                        PluginController.mark_useless(arg)
                    # these are parameters
                    elif isinstance(arg, kurt.scripts.Block):
                        PluginController.check_empty(block)

    @staticmethod
    def prepare_plugin(scratch):
        processing = set()
        pending = {}
        scratch.static = True
        for sprite in scratch.stage.sprites:
            for script in sprite.scripts:
                type = PluginController.hat_type(script)
                if type == "No Hat":
                    script.reachable = False
                elif type == "When I receive":
                    message = script.blocks[0].args[0]
                    if message == "":
                        script.reachable = False
                    else:
                        if message in pending.keys():
                            pending[message].add(script)
                        else:
                            pending[message] = {script}
                else:
                    processing.add(script)
        for script in scratch.stage.scripts:
            script.static = True
            type = PluginController.hat_type(script)
            if type == "No Hat":
                script.reachable = False
            elif type == "When I receive":
                message = script.blocks[0].args[0]
                if message == "":
                    script.reachable = False
                else:
                    if message in pending.keys():
                        pending[message].add(script)
                    else:
                        pending[message] = {script}
            else:
                processing.add(script)
        while len(processing) != 0:
            script = processing.pop()
            PluginController.mark_useless(script.blocks)
            for message in PluginController.get_messages(script.blocks):
                if message in pending.keys():
                    for message_script in pending[message]:
                        processing.add(message_script)
                    del pending[message]
            script.reachable = False
            #if everything after the hat block is empty,
            # the whole script is dead code
            for block in script.blocks:
                if not block.empty and block != script.blocks[0]:
                    script.reachable = True
        while len(pending) != 0:
            (message, scripts) = pending.popitem()
            for script in scripts:
                script.reachable = False
        scratch.plugin_prepared = True

    @staticmethod
    def pull_hat(hat_name, scripts):
        hat_scripts = []
        other = scripts
        for script in scripts:
            if PluginController.hat_type(script) == hat_name:
                hat_scripts.append(script)
                other.remove(script)
        return (hat_scripts, other)

    @staticmethod
    def save_png(image, image_name, sprite_name=''):
        """Save the image to disc and returns the relative path to the file.

        Use the companion function `get_image_html` in the view to get an html
        view for the image."""
        path = '{0}{1}.png'.format(sprite_name, image_name).replace('/', '_')
        image.save_png(path)
        os.chmod(path, 0444)  # Read-only archive file
        # Must be world readable for NGINX to serve the file.
        return path

    @staticmethod
    def save_png_dir(image, image_absolute_path_name):
        """Save the image to disc and returns the absolute path to the file.
        """

        image.save_png(image_absolute_path_name)
        os.chmod(image_absolute_path_name, 0400)  # Read-only archive file
        return image_absolute_path_name

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
