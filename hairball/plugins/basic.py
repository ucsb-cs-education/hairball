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


class BlockTypes(PluginBase):
    """Produces a count of each type of block contained in a scratch file."""

    def __init__(self, batch):
        super(BlockTypes, self).__init__(name='Basic Block Types', batch=batch)

    def getblock(self, block):
        blocks = collections.Counter()
        if (block.name == "EventHatMorph"):
            blocks[block.args[0]] = 1
        else:
            blocks[block.name] = 1
        for arg in block.args:
            if hasattr(arg, '__iter__'):
                blocks = blocks + self.getblocklist(arg)
            elif isinstance(arg, kurt.scripts.Block):
                blocks = blocks + self.getblock(arg)
        return blocks

    def getblocklist(self, blocklist):
        blocks = collections.Counter()
        for block in blocklist:
            blocks = blocks + self.getblock(block)
        return blocks

    def _process(self, scratch):
        blocks = collections.Counter()
        for sprite in scratch.stage.sprites:
            for script in sprite.scripts:
                blocks = blocks + self.getblocklist(script.blocks)
        p = ""
        for block, count in blocks.most_common():
            p = p + "{1:{2}} {0}".format(str(count), block, 30) + "\n"
        return '<pre>{0}</pre>'.format(p)
