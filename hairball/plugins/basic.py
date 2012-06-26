import collections
import kurt
from . import PluginBase


class Blocks(PluginBase):
    """Produces an aggregate count of blocks contained in a scratch file."""

    def __init__(self, batch):
        super(Blocks, self).__init__(name='Basic Blocks', batch=batch)

    def _process(self, scratch):
        r = ''
        for sprite in scratch.stage.sprites:
            r += self.to_scratch_blocks(sprite.name, sprite.scripts)
        r += self.to_scratch_blocks('Stage', sprite.scripts)
        return r


class History(PluginBase):
    """Produces a display for the history contained in a scratch file."""

    def __init__(self, batch):
        super(History, self).__init__(name='Basic History', batch=batch)

    def _process(self, scratch):
        return '<pre>{0}</pre>'.format(scratch.info['history'])


class Sprites(PluginBase):
    """Produces a visual of all sprites contained in a scratch file."""

    def __init__(self, batch):
        super(Sprites, self).__init__('Basic Sprites', batch=batch)

    def _process(self, scratch):
        return '<p>{0}</p>'.format(len(scratch.stage.sprites))


class DeadCode(PluginBase):
    """Produces a visual of the dead code for each sprite in a scratch file."""

    def __init__(self, batch):
        super(DeadCode, self).__init__('Basic Dead Code', batch=batch)

    def _process(self, scratch):
        scripts = []
        dead = ''
        for sprite in scratch.stage.sprites:
            for script in self.script_iter(sprite.scripts, True):
                scripts.append(script)
            if len(scripts) != 0:
                dead += self.to_scratch_blocks(sprite.name, scripts)
                scripts = []
        for script in self.script_iter(scratch.stage.scripts, True):
                scripts.append(script)
        if len(scripts) != 0:
                dead += self.to_scratch_blocks("stage", scripts)
        # if dead is empty, print "no dead code"
        if len(dead) == 0:
            return '<p>No Dead Code</p>'
        else:
            return dead


class Costumes(PluginBase):
    """Produces a view of the different costumes and backgrounds."""

    def __init__(self, batch):
        super(Costumes, self).__init__(name='Basic Costumes', batch=batch)

    def get_costumes(self, sprite):
        images = '<p>{0}</p> <br />'.format(sprite.name)
        for image in sprite.images:
            images += self.save_png(image, image.name, sprite.name)
        return images

    def _process(self, scratch):
        images = self.thumbnail
        for sprite in scratch.stage.sprites:
            images += self.get_costumes(sprite)
        images += self.get_costumes(scratch.stage)
        return images


class Changes(PluginBase):
    """Check if each sprite's properties were changed and if they were, whether or not they were initialized."""

    def __init__(self, batch):
        super(Changes, self).__init__(name='Basic Changes', batch=batch)

    def change(self, sprite, property):
        for script in sprite.scripts:
            for block in self.block_iter(script.blocks):
                temp = set([(block, "absolute"),
                            (block, "relative")])
                if temp & property:
                    return True
        return False

    def initialization(self, sprite, property):
        for script in sprite.scripts:
            if (script.blocks and script.blocks[0].args and
                script.blocks[0].args[0] == 'Scratch-StartClicked'):
                for block in self.block_iter(script.blocks):
                    if (block, "relative") in property:
                        return False
                    if (block, "absolute") in property:
                        return True
        return False

    def append_changes(self, sprite, property):
        attr_changes = ""
        change = self.change(sprite, self.BLOCKMAPPING[property])
        attr_changes += "{0} change: {1} <br />".format(property, change)
        if change:
            attr_changes += '<span class = "indent1"> Initialized: {0} <br /> </span>'.format(
                self.initialization(sprite, self.BLOCKMAPPING[property]))
        return attr_changes

    def _process(self, scratch):
        attribute_changes = ""
        attributes = ["position", "orientation",
                      "costume", "volume", "tempo", "variables"]
        for sprite in scratch.stage.sprites:
            attribute_changes += sprite.name + "<br />"
            for property in attributes:
                attribute_changes += self.append_changes(sprite, property)
            attribute_changes += "<br />"
        attribute_changes += "script <br />"
        for property in attributes:
            attribute_changes += self.append_changes(scratch.stage, property)
        return '<p>{0}</p>'.format(attribute_changes)


class BlockTypes(PluginBase):
    """Produces a count of each type of block contained in a scratch file."""

    def __init__(self, batch):
        super(BlockTypes, self).__init__(name='Basic Block Types', batch=batch)

    def get_list_count(self, block_list):
        blocks = collections.Counter()
        for block in self.block_iter(block_list):
            blocks.update({block: 1})
        return blocks

    def _process(self, scratch):
        blocks = collections.Counter()
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            blocks += self.get_list_count(script.blocks)
        p = ""
        for block, count in blocks.most_common():
            p = p + "{1:{2}} {0}".format(str(count), block, 30) + '<br />'
        return '<p>{0}</p>'.format(p)
