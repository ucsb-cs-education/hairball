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

    def EventHatType(self,k):
        name = k.name
        if (name == "EventHatMorph"):
                name = k.args[0]
        return name

    def _process(self, scratch):
        block_types = {}
        length = 0
        name = ""
        for x in scratch.stage.sprites:
            for y in x.scripts:
                for z in y.blocks:
                    name = self.EventHatType(z)
                    if (name not in block_types):
                        block_types[name] = 1
                        if (len(name)> length):
                            length = len(name)
                    else:
                        block_types[name] = block_types[name] + 1
        length = length + 5
        p = ""
        keys =  sorted(block_types, key=block_types.__getitem__, reverse=True)
        for b in keys:
            p = p + "{1:{2}} {0}".format(str(block_types[b]), b, length)
            p = p + "\n"
        return '<pre>{0}</pre>'.format(p)
