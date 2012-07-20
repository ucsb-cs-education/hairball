import collections
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
        if len(data['deadcode']) == 0:
            dead = '<p>No Dead Code</p>'
        else:
            for sprite in data['deadcode'].keys():
                dead += self.to_scratch_blocks(
                    sprite, data['deadcode'][sprite])
        return dead


class DeadCode(PluginController):
    """Dead Code

    Shows all of the dead code for each sprite in a scratch file.
    """
    @PluginWrapper(html=DeadCodeView)
    def analyze(self, scratch):
        sprite_scripts = []
        sprite_dict = {}
        for sprite in scratch.stage.sprites:
            for script in sprite.scripts:
                if script.reachable == False:
                    sprite_scripts.append(script)
            if len(sprite_scripts) != 0:
                sprite_dict[sprite.name] = sprite_scripts
                sprite_scripts = []
        for script in scratch.stage.scripts:
            if script.reachable == False:
                sprite_scripts.append(script)
        if len(sprite_scripts) != 0:
            sprite_dict["stage"] = sprite_scripts
        return self.view_data(deadcode=sprite_dict)


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
