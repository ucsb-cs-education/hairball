from collections import Counter
import copy
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
    @PluginWrapper(html=BlockTypesView)
    def analyze(self, scratch):
        blocks = Counter()
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            for name, level, block in self.block_iter(script.blocks):
                blocks.update({name: 1})
        return self.view_data(types=blocks.most_common())


class BlockTotals(PluginController):
    """Block Totals

    Produces a count of each type of block contained in all the scratch files.
    """
    def __init__(self):
        super(BlockTotals, self).__init__()
        self.blocks = {}

    def finalize(self):
        file = open('blocktypes.txt', 'w')
        file.write("activity, pair, ")
        for key in self.BLOCKCOUNTER.keys():
            file.write(key)
            file.write(', ')
        for ((group, project), blockcount) in self.blocks.items():
            file.write('\n')
            file.write(project)
            file.write(', ')
            file.write(group)
            for block in self.BLOCKCOUNTER.keys():
                file.write(', ')
                file.write(str(blockcount[block]))

    def analyze(self, scratch):
        self.blocks[(scratch.group, scratch.project)] = copy.deepcopy(
            self.BLOCKCOUNTER)
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            for name, level, block in self.block_iter(script.blocks):
                self.blocks[(scratch.group, scratch.project)].update({name: 1})
        return self.view_data(types=self.blocks)


class DeadCodeView(PluginView):
    def view(self, data):
        dead = ""
        (dynamic, deadcode) = data['deadcode']
        if len(deadcode) == 0:
            dead = '<p>No Dead Code</p>'
        else:
            if dynamic:
                dead = '<p>Warning: Contains dynamic broadcast messages</p>'
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

    def get_useless(self, blocklist):
        useless = []
        for block in blocklist:
            if isinstance(block, kurt.scripts.Block):
                if block.empty:
                    useless.append(block)
                else:
                    for arg in block.args:
                        if hasattr(arg, '__iter__'):
                            useless.extend(self.get_useless(arg))
                        elif isinstance(arg, kurt.scripts.Block):
                            useless.extend(self.get_useless([arg]))
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
        for sprite in data['scripts'].keys():
            script_images += self.to_scratch_blocks(
                sprite, data["scripts"][sprite])
        return script_images


class ScriptImages(PluginController):
    """The Script Images

    Shows all of the scripts for each sprite in a scratch file.
    """
    @PluginWrapper(html=ScriptImagesView)
    def __init__(self):
        super(ScriptImages, self).__init__()
        self.script_images = {}

    def finalize(self):
        file = open('scriptimages.html', 'w')
        for sprite in self.script_images.keys():
            file.write(
                self.to_scratch_blocks(sprite, self.script_images[sprite]))

    def analyze(self, scratch):
        for sprite in scratch.stage.sprites:
            self.script_images[sprite.name] = []
            for script in sprite.scripts:
                self.script_images[sprite.name].append(script)
        self.script_images["stage"] = []
        for script in scratch.stage.scripts:
            self.script_images["stage"].append(script)
        return self.view_data(scripts=self.script_images)
