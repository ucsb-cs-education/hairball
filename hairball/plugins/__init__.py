import kurt
import os
from collections import Counter
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
    IMG_TMPL = '<img class="scratch-image" src="{0}" />\n<br />\n'
    SUBHEADING = '<div class="subheading">{0}</div>'

    BLOCKCOUNTER = Counter({
        "go to x: %n y: %n": 0,
        "go to %m": 0,
        "glide %n secs to x: %n y: %n": 0,
        "change x by %n": 0,
        "set x to %n": 0,
        "change y by %n": 0,
        "set y to %n": 0,
        "if on edge bounce": 0,
        "x position": 0, "y position": 0,
        "direction": 0,
        "when green flag clicked": 0,
        "when %k key pressed": 0,
        "when %m clicked": 0,
        "wait %n secs": 0, "forever": 0,
        "repeat %n": 0, "broadcast": 0,
        "broadcast %e and wait": 0,
        "when I receive %e": 0,
        "forever if %b": 0,
        "if %b": 0, "if %b": 0,
        "wait until %b": 0,
        "repeat until %b": 0,
        "stop script": 0, "stop all": 0,
        "switch to background %l": 0,
        "next background": 0,
        "background #": 0,
        "change %g effect by %n": 0,
        "set %g effect to %n": 0,
        "clear graphic effects": 0,
        "switch to costume %l": 0,
        "next costume": 0, "costume #": 0,
        "say %s for %n secs": 0,
        "say %s": 0,
        "think %s for %n secs": 0,
        "think %s": 0,
        "change %g effect by %n": 0,
        "set %g effect to %n": 0,
        "clear graphic effects": 0,
        "change size by %n": 0,
        "set size to %n %": 0,
        "size": 0, "show": 0, "hide": 0,
        "go to front": 0, "go back %n layers": 0,
        "ask %s and wait": 0, "answer": 0,
        "mouse x": 0, "mouse y": 0,
        "mouse down?": 0, "key %k pressed?": 0,
        "reset timer": 0, "timer": 0,
        "%a of %m": 0, "loudness": 0, "loud?": 0,
        "sensor %h ?": 0, "touching %m ?": 0,
        "touching color %C ?": 0,
        "color %C is touching %C ?": 0,
        "distance to %m": 0, "play sound %S": 0,
        "play sound %S until done": 0,
        "stop all sounds": 0,
        "play drum %D for %n beats": 0,
        "rest for %n beats": 0,
        "play note %N for %n beats": 0,
        "set instrument to %I": 0,
        "change volume by %n": 0,
        "set volume to %n %": 0,
        "volume": 0, "change tempo by %n": 0,
        "set tempo to %n bpm": 0, "tempo": 0,
        "%n + %n": 0, "%n - %n": 0, "%n * %n": 0,
        "%n / %n": 0, "pick random %n to %n": 0,
        "%s < %s": 0, "%s = %s": 0, "%s > %s": 0,
        "%b and %b": 0, "%b or %b": 0, "not %b": 0,
        "join %s %s": 0, "letter %n of %s": 0,
        "length of %s": 0, "%n mod %n": 0,
        "round %n": 0, "%f of %n": 0,
        "A block with color %C and color %c:": 0,
        "clear pen trails": 0, "pen down": 0,
        "pen up": 0, "set pen color to %c": 0,
        "change pen color by %n": 0,
        "set pen color to %n": 0,
        "change pen shade by %n": 0,
        "set pen shade to %n": 0,
        "change pen size by %n": 0,
        "set pen size to %n": 0,
        "stamp": 0, "show variable %v": 0,
        "hide variable %v": 0, "%v": 0,
        "change %v by %n": 0,
        "set %v to %s": 0})

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

    MAPPING = {"forward:": "move %n steps",
               "turnRight:": "turn clockwise %n degrees",
               "turnLeft:": "turn counterclockwise %n degrees",
               "heading:": "point in direction %d",
               "pointTowards:": "point towards %m",
               "gotoX:y:": "go to x: %n y: %n",
               "gotoSpriteOrMouse:": "go to %m",
               "glideSecs:toX:y:elapsed:from:": "glide %n secs to x: %n y: %n",
               "changeXposBy:": "change x by %n", "xpos:": "set x to %n",
               "changeYposBy:": "change y by %n", "ypos:": "set y to %n",
               "bounceOffEdge": "if on edge bounce",
               "xpos": "x position", "ypos": "y position",
               "EventHatMorph": "when green flag clicked",
               "KeyEventHatMorph": "when %k key pressed",
               "MouseClickEventHatMorph": "when %m clicked",
               "wait:elapsed:from:": "wait %n secs",
               "doForever": "forever", "doRepeat": "repeat %n",
               "broadcast:": "broadcast", "doIfElse": "if %b",
               "doBroadcastAndWait": "broadcast %e and wait",
               "EventHatMorph": "when I receive %e",
               "doForeverIf": "forever if %b", "doIf": "if %b",
               "doWaitUntil": "wait until %b",
               "doUntil": "repeat until %b",
               "doReturn": "stop script",
               "stopAll": "stop all", "heading": "direction",
               "showBackground:": "switch to background %l",
               "nextBackground": "next background",
               "backgroundIndex": "background #",
               "changeGraphicEffect:by:": "change %g effect by %n",
               "setGraphicEffect:to:": "set %g effect to %n",
               "filterReset": "clear graphic effects",
               "lookLike:": "switch to costume %l",
               "nextCostume": "next costume",
               "costumeIndex": "costume #",
               "say:duration:elapsed:from:": "say %s for %n secs",
               "say:": "say %s", "think:": "think %s",
               "think:duration:elapsed:from:": "think %s for %n secs",
               "changeGraphicEffect:by:": "change %g effect by %n",
               "setGraphicEffect:to:": "set %g effect to %n",
               "filterReset": "clear graphic effects",
               "changeSizeBy:": "change size by %n",
               "setSizeTo:": "set size to %n %",
               "scale": "size", "show": "show", "hide": "hide",
               "comeToFront": "go to front",
               "goBackByLayers:": "go back %n layers",
               "doAsk": "ask %s and wait",
               "answer": "answer", "mouseX": "mouse x",
               "mouseY": "mouse y", "mousePressed": "mouse down?",
               "keyPressed:": "key %k pressed?",
               "timerReset": "reset timer", "timer": "timer",
               "getAttribute:of:": "%a of %m",
               "soundLevel": "loudness",
               "isLoud": "loud?", "sensor:": "%H sensor value",
               "sensorPressed:": "sensor %h ?",
               "touching:": "touching %m ?",
               "touchingColor:": "touching color %C ?",
               "color:sees:": "color %C is touching %C ?",
               "distanceTo:": "distance to %m",
               "playSound:": "play sound %S",
               "doPlaySoundAndWait": "play sound %S until done",
               "stopAllSounds": "stop all sounds",
               "drum:duration:elapsed:from:": "play drum %D for %n beats",
               "rest:elapsed:from:": "rest for %n beats",
               "noteOn:duration:elapsed:from:": "play note %N for %n beats",
               "midiInstrument:": "set instrument to %I",
               "changeVolumeBy:": "change volume by %n",
               "setVolumeTo:": "set volume to %n %",
               "volume": "volume", "tempo": "tempo",
               "changeTempoBy:": "change tempo by %n",
               "setTempoTo:": "set tempo to %n bpm",
               "+": "%n + %n", "-": "%n - %n", "*": "%n * %n",
               "<": "%s < %s", "/": "%n / %n",
               "randomFrom:to:": "pick random %n to %n",
               "=": "%s = %s", "&": "%b and %b", "`": "%b or %b",
               ">": "%s > %s", "not": "not %b",
               "concatenate:with:": "join %s %s",
               "letter:of:": "letter %n of %s",
               "stringLength:": "length of %s",
               "\\": "%n mod %n", "rounded": "round %n",
               "computeFunction:of:": "%f of %n",
               "thingwithColor:andColor:":
               "A block with color %C and color %c:",
               "clearPenTrails": "clear pen trails",
               "putPenDown": "pen down",
               "putPenUp": "pen up",
               "penColor:": "set pen color to %c",
               "changePenHueBy:": "change pen color by %n",
               "setPenHueTo:": "set pen color to %n",
               "changePenShadeBy:": "change pen shade by %n",
               "setPenShadeTo:": "set pen shade to %n",
               "changePenSizeBy:": "change pen size by %n",
               "penSize:": "set pen size to %n",
               "stampCostume": "stamp", "readVariable": "%v",
               "showVariable:": "show variable %v",
               "hideVariable:": "hide variable %v",
               "changeVariable": "change %v by %n",
               "changeVariable": "set %v to %s"}

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
                yield('when green flag clicked', 0, block)
            else:
                yield("when I receive %e", 0, block)
        elif block.name == 'changeVariable':
            if 'setVar' in str(block.args[1]):
                yield("set %v to %s", level, block)
            else:
                yield("change %v by %n", level, block)
        # skip comments
        elif block.name != "":
#if this is a distinct block, use the original name
            yield (PluginController.MAPPING[block.name], level, block)
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
                return "when green flag clicked"
            else:
                return "when I receive %e"
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
            elif type == "when I receive %e":
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

    @staticmethod
    def to_scratch_blocks(heading, scripts):
        """Output the scripts in an html-ready scratch blocks format."""
        data = []
        for script in scripts:
            data.append('<div class="float scratchblocks">{0}</div>'
                        .format(script.to_block_plugin()))
        heading = PluginController.SUBHEADING.format(heading)
        return ('<div>\n{0}\n<div>{1}</div>\n<div class="clear"></div>\n'
                '</div>\n').format(heading, ''.join(data))

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
