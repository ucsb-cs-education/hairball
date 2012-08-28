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
    BLOCKMAPPING = {"position": set([("move %n steps", "relative"),
                                     ("go to x:%n y:%n", "absolute"),
                                     ("go to %m", "relative"),
                                     ("glide %n secs to x:%n y:%n",
                                      "relative"),
                                     ("change x by %n", "relative"),
                                     ("x position", "absolute"),
                                     ("change y by %n", "relative"),
                                     ("y position", "absolute")]),
                    "orientation": set([("turn clockwise %n degrees",
                                         "relative"),
                                        ("turn counterclockwise %n degrees",
                                         "relative"),
                                        ("point in direction %d", "absolute"),
                                        ("point towards %m", "relative")]),
                    "costume": set([("switch to background %l", "absolute"),
                                    ("next background", "relative"),
                                    ("switch to costume %l", "absolute"),
                                    ("next costume", "relative")]),
                    "size": set([("change size by %n", "relative"),
                                 ("set size to %n", "absolute")])}

    @staticmethod
    def block_iter(block_list, level=0):
        for block in block_list:
            if isinstance(block, kurt.scripts.Block):
                for b in PluginController.get_block(block, level):
                    yield b

    @staticmethod
    def get_block(block, level):
        if block.name == 'EventHatMorph':
            if block.args[0] == 'Scratch-StartClicked':
                yield('when green flag clicked', 0, block)
            else:
                yield("when I receive %e", 0, block)
        elif block.name == 'changeVariable':
            if 'setVar' in str(block.args[1]):
                yield('set %v by %n', level, block)
            else:
                yield(block.type.text, level, block)
        elif block.name == 'doIfElse':
            yield('if %b else', level, block)
        elif block.name != "":
            yield (block.type.text, level, block)
            for arg in block.args:
                if hasattr(arg, '__iter__'):
                    for b in PluginController.block_iter(arg, level + 1):
                        yield b
                elif isinstance(arg, kurt.scripts.Block):
                    for b in PluginController.get_block(arg, level):
                        yield b

    @staticmethod
    def get_broadcast(script_list):
        scripts = script_list[:]
        messages = {}
        message = ""
        for script in scripts:
            gen = PluginController.block_iter(script.blocks)
            for name, level, block in gen:
                if "broadcast %e" in name:
                    if isinstance(block.args[0], kurt.scripts.Block):
                        message = "dynamic"
                    else:
                        message = block.args[0].lower()
                    if message not in messages.keys():
                        messages[message] = set()
                        messages[message].add(script)
                    else:
                        messages[message].add(script)
        return messages

    @staticmethod
    def broadcastreceive(script_list):
        scripts = script_list[:]
        receive = PluginController.get_receive(scripts)
        never_r = PluginController.get_broadcast(scripts)
        never_b = {}
        for (message, scripts) in receive.items():
#            if message == "final scene":
#                del receive[message]
#                if message in never_r.keys():
#                    del never_r[message]
            if message in never_r.keys():
                del never_r[message]
            else:
                never_b[message] = scripts
        return (never_r, never_b)

    @staticmethod
    def check_empty(word):
        if len(word) == 0:
            return True
        else:
            for letter in word:
                if letter != " ":
                    return False
        return True

    @staticmethod
    def get_receive(script_list):
        messages = {}
        scripts = script_list[:]
        for script in scripts:
            if PluginController.hat_type(script) == "when I receive %e":
                message = script.blocks[0].args[0].lower()
                if message not in messages.keys():
                    messages[message] = set()
                messages[message].add(script)
        return messages

    @staticmethod
    def mark_scripts(scratch):
        processing = set()
        pending = {}
        scratch.static = True
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        # Find scripts without hat blocks
        for script in scripts:
            if PluginController.hat_type(script) == "No Hat":
                script.reachable = False
            elif PluginController.hat_type(script) == "when I receive %e":
                message = script.blocks[0].args[0].lower()
                script.reachable = True
                if message in pending.keys():
                    pending[message].add(script)
                else:
                    pending[message] = {script}
            else:
                script.reachable = True
                processing.add(script)
        while len(processing) != 0:
            script = processing.pop()
            for message in PluginController.get_broadcast([script]).keys():
                if message in pending.keys():
                    for s in pending[message]:
                        processing.add(s)
                    del pending[message]
        while len(pending) != 0:
            (message, scripts) = pending.popitem()
            for script in scripts:
                script.reachable = False
        scratch.plugin_prepared = True

    @staticmethod
    def hat_type(script):
        if script.blocks[0].name == 'EventHatMorph':
            if script.blocks[0].args[0] == 'Scratch-StartClicked':
                return "when green flag clicked"
            else:
                return "when I receive %e"
        elif 'EventHatMorph' in script.blocks[0].name:
            return script.blocks[0].name
        else:
            return "No Hat"

    @staticmethod
    def pull_hat(hat_name, scripts):
        hat_scripts = []
        other = scripts[:]
        for script in other:
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
            self.mark_scripts(scratch)
        return self.analyze(scratch, **kwargs)

    def view_data(self, **kwargs):
        kwargs['_name'] = self.name
        kwargs['_description'] = self.description
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
