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
        filename = ''
        for image in sprite.images:
            filename = '{0}{1}.png'.format(
                sprite.name, image.name).replace('/', '_')
            image.save_png(filename)
            images += '<img class="scratch-image" src="{0}" />'.format(
                filename)
            images += '<br />'
        return images

    def _process(self, scratch):
        filename = '{0}_thumbnail.png'.format(scratch.name).replace('/', '_')
        images = '<img class="scratch-image" src="{0}" /> '.format(filename)
        images += '<br />'
        scratch.info['thumbnail'].save_png(filename)
        for sprite in scratch.stage.sprites:
            images += self.get_costumes(sprite)
        images += self.get_costumes(scratch.stage)
        return images


class Changes(PluginBase):
    """Produces a count of the number of property changes for each sprite."""

    def __init__(self, batch):
        super(Changes, self).__init__(name='Basic Changes', batch=batch)

    def Change(self, sprite, set):
        change = False
        for script in sprite.scripts:
            for block in script.blocks:
                if block.name in set:
                    change = True
        return change

    def _process(self, scratch):
        attribute_changes = ""
        for sprite in scratch.stage.sprites:
            attribute_changes += sprite.name + "<br />"
            attribute_changes += "Position change: {0} <br />".format(
                self.Change(sprite, self.BLOCKMAPPING["position"]))
            attribute_changes += "Orientation change: {0} <br />".format(
                self.Change(sprite, self.BLOCKMAPPING["orientation"]))
            attribute_changes += "Costume change: {0} <br />".format(
                self.Change(sprite, self.BLOCKMAPPING["costume"]))
            attribute_changes += "Volume change: {0} <br />".format(
                self.Change(sprite, self.BLOCKMAPPING["volume"]))
            attribute_changes += "Tempo change: {0} <br />".format(
                self.Change(sprite, self.BLOCKMAPPING["tempo"]))
            attribute_changes += "Variables change: {0} <br />".format(
                self.Change(sprite, self.BLOCKMAPPING["variables"]))
            attribute_changes += '<br />'
        attribute_changes += "stage <br />"
        attribute_changes += "Position change: {0} <br />".format(
            self.Change(scratch.stage, self.BLOCKMAPPING["position"]))
        attribute_changes += "Orientation change: {0} <br />".format(
            self.Change(scratch.stage, self.BLOCKMAPPING["orientation"]))
        attribute_changes += "Costume change: {0} <br />".format(
            self.Change(scratch.stage, self.BLOCKMAPPING["costume"]))
        attribute_changes += "Volume change: {0} <br />".format(
            self.Change(scratch.stage, self.BLOCKMAPPING["volume"]))
        attribute_changes += "Tempo change: {0} <br />".format(
            self.Change(scratch.stage, self.BLOCKMAPPING["tempo"]))
        attribute_changes += "Variables change: {0} <br />".format(
            self.Change(scratch.stage, self.BLOCKMAPPING["variables"]))
        return '<p>{0}</p>'.format(attribute_changes)


class BlockTypes(PluginBase):
    """Produces a count of each type of block contained in a scratch file."""

    def __init__(self, batch):
        super(BlockTypes, self).__init__(name='Basic Block Types', batch=batch)

    def get_block(self, block):
        blocks = collections.Counter()
        if block.name == 'EventHatMorph':
            if block.args[0] == 'Scratch-StartClicked':
                name = 'When green flag clicked'
            else:
                name = 'When I receive'
            blocks[name] = 1
        else:
            blocks[block.name] = 1
        for arg in block.args:
            if hasattr(arg, '__iter__'):
                blocks += self.get_block_list(arg)
            elif isinstance(arg, kurt.scripts.Block):
                blocks += self.get_block(arg)
        return blocks

    def get_block_list(self, block_list):
        blocks = collections.Counter()
        for block in block_list:
            blocks += self.get_block(block)
        return blocks

    def _process(self, scratch):
        blocks = collections.Counter()
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            blocks += self.get_block_list(script.blocks)
        p = ""
        for block, count in blocks.most_common():
            p = p + "{1:{2}} {0}".format(str(count), block, 30) + '<br />'
        return '<p>{0}</p>'.format(p)
