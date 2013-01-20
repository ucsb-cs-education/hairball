from collections import Counter
import copy
from . import HairballPlugin, PluginView, PluginWrapper


class BlockTypesView(PluginView):
    def view(self, data):
        blocks = ""
        for block, count in data['types']:
            blocks += "{1:{2}} {0}".format(str(count), block, 30) + '<br />'
        return '<p>{0}</p>'.format(blocks)


class BlockTypes(HairballPlugin):
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


class BlockTotals(HairballPlugin):
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
        blocks = Counter()
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            for name, level, block in self.block_iter(script.blocks):
                blocks.update({name: 1})
        if hasattr(scratch, 'group') and hasattr(scratch, 'project'):
            self.blocks[(scratch.group,
                         scratch.project)] = copy.deepcopy(blocks)
        return self.view_data(types=blocks)


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
                if len(deadcode[sprite]) != 0:
                    dead += self.to_scratch_blocks(
                        sprite, deadcode[sprite])
        return dead


class DeadCode(HairballPlugin):
    """Dead Code

    Shows all of the dead code for each sprite in a scratch file.
    """
    def __init__(self):
        super(DeadCode, self).__init__()
        self.dead = {}

    def finalize(self):
        file = open('deadcode.txt', 'w')
        file.write("activity, pair, dynamic?, sprites with dead code\n")
        for ((group, project), (dynamic, sprite_dict)) in self.blocks.items():
            file.write('\n')
            file.write(project)
            file.write(', ')
            file.write(group)
            file.write(', ')
            file.write(dynamic)
            for key in sprite_dict.keys():
                file.write(', ')
                file.write(key)

    @PluginWrapper(html=DeadCodeView)
    def analyze(self, scratch):
        sprites = {}
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            if script.morph.name not in sprites.keys():
                sprites[script.morph.name] = []
            if not script.reachable:
                sprites[script.morph.name].append(script)
        if "dynamic" in self.get_broadcast(scripts):
            dynamic = True
        else:
            dynamic = False
        if hasattr(scratch, 'group') and hasattr(scratch, 'project'):
            self.dead[(scratch.group,
                       scratch.project)] = (dynamic, copy.deepcopy(sprites))
        return self.view_data(deadcode=(dynamic, sprites))


class ScriptImagesView(PluginView):
    def view(self, data):
        script_images = ""
        for sprite in data['scripts'].keys():
            script_images += self.to_scratch_blocks(
                sprite, data["scripts"][sprite])
        return script_images


class ScriptImages(HairballPlugin):
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
