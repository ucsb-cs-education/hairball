import collections
from . import PluginBase


class DisplayBlocks(PluginBase):
    """Produces a visual of all the scripts in the file."""

    def __init__(self, batch):
        super(DisplayBlocks, self).__init__(name='Basic Blocks', batch=batch)

    def _process(self, scratch):
        r = ''
        for sprite in scratch.stage.sprites:
            r += self.to_scratch_blocks(sprite.name, sprite.scripts)
        r += self.to_scratch_blocks('Stage', sprite.scripts)
        return r


class FileHistory(PluginBase):
    """Produces a display for the history contained in a scratch file."""

    def __init__(self, batch):
        super(FileHistory, self).__init__(name='Basic History', batch=batch)

    def _process(self, scratch):
        return '<pre>{0}</pre>'.format(scratch.info['history'])


class SpriteCount(PluginBase):
    """Outputs the number of sprites in a scratch file."""

    def __init__(self, batch):
        super(SpriteCount, self).__init__('Basic Sprites', batch=batch)

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
    """Check if properties were changed and if so, if they were initialized."""

    def __init__(self, batch):
        super(Changes, self).__init__(name='Basic Changes', batch=batch)

    def gen_change(self, sprite, property):
        greenflag = False
        bandw = False
        for script in sprite.scripts:
            greenflag = self.starts_green_flag(script)
            for name, level, block in self.block_iter(script.blocks):
                if name == 'doBroadcastAndWait':
                    bandw = True
                temp = set([(name, "absolute"),
                            (name, "relative")])
                if temp & property:
                    if (name, "absolute") in property and not bandw:
                        if level == 0 and greenflag:
                            return (True, True)
                    else:
                        return (True, False)
        return (False, False)

    def variable_change(self, sprite, global_vars):
        bandw = False
        local_vars = dict()
        for key in sprite.vars.keys():
            local_vars[key] = "uninitialized"
        # if there are no local or global variables,
        # there won't be any variable change
        if len(global_vars) == 0 and len(local_vars) == 0:
            return (False, False), global_vars
        # otherwise, check for initilization
        for script in sprite.scripts:
            if self.starts_green_flag(script):
                for name, level, block in self.block_iter(script):
                    if name == 'doBroadcastAndWait':
                        bandw = True
                    #if we're setting a var in level 0
                    #and we're not past a broadcast and wait
                    if name == 'setVariable' and level == 0 and not bandw:
                        variable = block.args[0]
                        if variable in local_vars.keys():
                            local_vars[variable] = 'set'
                        if variable in global_vars.keys():
                            global_vars[variable] = 'set'
                    elif name == 'setVariable' or name == 'changeVariable':
                        variable = block.args[0]
                        if variable in local_vars.keys():
                            if local_vars[variable] == "uninitialized":
                                local_vars[variable] = 'changed'
                        if variable in global_vars.keys():
                            if global_vars[variable] == "uninitialized":
                                global_vars[variable] = 'changed'
        #if any value in out local_vars is changed, then we didn't initialize
        if 'changed' in local_vars.values():
            return (True, False), global_vars
        elif 'set' in local_vars.values():
            return (True, True), global_vars
        else:
            #this doesn't take into account any action
            #by this sprite on the global variables
            return (False, False), global_vars

    def visibility_change(self, sprite):
        bandw = False
        initialized = False
        changed = False
        for script in sprite.scripts:
            if self.starts_green_flag(script):
                for name, level, block in self.block_iter(script):
                    if name == 'doBroadcastAndWait':
                        bandw = True
                    if name == "show" or name == "hide":
                        if level == 0 and not bandw:
                            changed, initialized = True, True
                        else:
                            changed = True
        return (changed, initialized)

    def add(self, property, (changed, initialized)):
        attr_changes = "{0} change: {1} <br />".format(property, changed)
        if changed: 
            attr_changes += '<span class = "indent1"> Initialized: '
            attr_changes += '{0} <br /> </span>'.format(initialized)
        return attr_changes

    def sprite_changes(self, sprite, global_variables):
        sprite_attr = sprite.name + "<br />"
        general = ["position", "orientation", "costume", "size"]
        for property in general:
            sprite_attr += self.add(property, self.gen_change(
                    sprite, self.BLOCKMAPPING[property]))
        sprite_attr += self.add("visibility", self.visibility_change(sprite))
        var_changes, global_variables = self.variable_change(sprite, global_variables)
        sprite_attr += self.add("variables", var_changes) 
        sprite_attr += "<br />"
        return sprite_attr, global_variables

    def _process(self, scratch):
        attribute_changes = ""
        global_vars = dict()
        for key in scratch.stage.vars.keys():
            global_vars[key] = "uninitialized"
        for sprite in scratch.stage.sprites:
            sprite_attr, global_variables = self.sprite_changes(sprite, global_vars)
            attribute_changes += sprite_attr
        attribute_changes += self.add("background", self.gen_change(
                scratch.stage, self.BLOCKMAPPING["costume"]))
        attribute_changes += "<br />"
        # check global/stage variables
        # right now we're not looking at what the stage changes
        var_change, global_vars = self.variable_change(scratch.stage, global_vars)
        if "changed" in global_vars.values():
            global_change = (True, False)
        elif "set" in global_vars.values():
            global_change = (True, True)
        else:
            global_change = (False, False)
        attribute_changes += self.add("global variables", global_change)
        return '<p>{0}</p>'.format(attribute_changes)


class BlockTypes(PluginBase):
    """Produces a count of each type of block contained in a scratch file."""

    def __init__(self, batch):
        super(BlockTypes, self).__init__(name='Basic Block Types', batch=batch)

    def get_list_count(self, block_list):
        blocks = collections.Counter()
        for block in self.block_iter(block_list):
            blocks.update({block[0]: 1})
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
