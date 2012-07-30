import collections
import kurt
from . import PluginController, PluginView, PluginWrapper


class BlockTypesView(PluginView):
    def view(self, data):
        blocks = ""
        for block, count in data['types']:
            blocks += "{1:{2}} {0}".format(str(count), block, 30) + '<br />'
        return '<p>{0}</p>'.format(blocks)


class BlockTypes(PluginController):
    """Block Types

    Produces a count of each type of block contained in a scratch file.
    """
    def get_list_count(self, block_list):
        blocks = collections.Counter()
        for block in self.block_iter(block_list):
            blocks.update({block[0]: 1})
        return blocks

    @PluginWrapper(html=BlockTypesView)
    def analyze(self, scratch):
        blocks = collections.Counter()
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            blocks += self.get_list_count(script.blocks)
        return self.view_data(types=blocks.most_common())


class DeadCodeView(PluginView):
    def view(self, data):
        dead = ""
        (dynamic, deadcode) = data['deadcode']
        if len(deadcode) == 0:
            dead = '<p>No Dead Code</p>'
        else:
            if dynamic:
                dead = '<p>Warning: Contains dynamic broadcast messages</p>'
            else:
                dead = '<p>No dynamic broadcast messages</p>'
            for sprite in deadcode.keys():
                dead += self.to_scratch_blocks(
                    sprite, deadcode[sprite])
        return dead


class DeadCode(PluginController):
    """Dead Code

    Shows all of the dead code for each sprite in a scratch file.
    """
    def check_dynamic(self, scratch):
        messages = set()
        for sprite in scratch.stage.sprites:
            for script in sprite.scripts:
                for message in self.get_messages(script.blocks):
                    messages.add(message)
        for script in scratch.stage.scripts:
            for message in self.get_messages(script.blocks):
                messages.add(message)
        if "dynamic" in messages:
            return True
        else:
            return False

    def check_empty(self, block):
        arithmetic = set(['+', '-', '*', '/', '<', '=', '>', '\\', 'rounded'])
        logic = set(['&', '`', 'not', 'doIf', 'doIfElse',
                     'doForeverIf', 'doWaitUntil', 'doUntil'])
        objects = set(['gotoSpriteOrMouse:', 'touching:', 'distanceTo:'])
        strings = set(['think:duration:elapsed:from:', 'think:', 'say:',
                       'say:duration:elapsed:from:', 'doAsk',
                       'concatenate:with:', 'stringLength:',
                       'broadcast:', 'doBroadcastAndWait', 'When I receive'])
        if block.name == 'letter:of:':
            if '0' in block.args or '' in block.args:
                return True
        elif block.name in arithmetic:
            if block.name == 'rounded':
                if block.args == [0]:
                    return True
            elif block.args == [0, 0]:
                return True
        elif block.name in logic:
            if block.name == '&' or block.name == '`':
                if block.args == [False, False]:
                    return True
            elif False in block.args:
                return True
        elif block.name in objects:
            if None in block.args:
                return True
        elif block.name in strings:
            if "" in block.args:
                return True
        for arg in block.args:
            if isinstance(arg, kurt.scripts.Block):
                return self.check_empty(arg)
        return False

    def get_useless(self, blocklist):
        useless = []
        for block in blocklist:
            if self.check_empty(block):
                useless.append(block)
            else:
                for arg in block.args:
                    # lists of blocks are the stuff inside of c blocks
                    if hasattr(arg, '__iter__'):
                        useless.extend(self.get_useless(arg))
                # these are parameters
                    elif isinstance(arg, kurt.scripts.Block):
                        if self.check_empty(block):
                            useless.append(block)
        return useless

    @PluginWrapper(html=DeadCodeView)
    def analyze(self, scratch):
        sprite_scripts = []
        sprite_dict = {}
        for sprite in scratch.stage.sprites:
            for script in sprite.scripts:
                if script.reachable is False:
                    sprite_scripts.append(script)
                else:
                    sprite_scripts.extend(self.get_useless(script.blocks))
            if len(sprite_scripts) != 0:
                sprite_dict[sprite.name] = sprite_scripts
                sprite_scripts = []
        for script in scratch.stage.scripts:
            if script.reachable is False:
                sprite_scripts.append(script)
            else:
                sprite_scripts.extend(self.get_useless(script.blocks))
        if len(sprite_scripts) != 0:
            sprite_dict["stage"] = sprite_scripts
        dynamic = self.check_dynamic(scratch)
        return self.view_data(deadcode=(dynamic, sprite_dict))


class ScriptImagesView(PluginView):
    def view(self, data):
        script_images = ""
        for sprite, scripts in data['scripts']:
            script_images += self.to_scratch_blocks(sprite, scripts)
        return script_images


class ScriptImages(PluginController):
    """The Script Images

    Shows all of the scripts for each sprite in a scratch file.
    """
    @PluginWrapper(html=ScriptImagesView)
    def analyze(self, scratch):
        sprite_scripts = []
        scripts = []
        for sprite in scratch.stage.sprites:
            for script in sprite.scripts:
                sprite_scripts.append(script.to_block_plugin())
            scripts.append((sprite.name, sprite_scripts))
            sprite_scripts = []
        for script in scratch.stage.scripts:
            sprite_scripts.append(script.to_block_plugin())
        scripts.append(("stage", sprite_scripts))
        return self.view_data(scripts=scripts)
