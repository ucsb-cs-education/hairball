"""This module provides plugins for checking initialization."""

from . import HairballPlugin


def partition_scripts(scripts, start_type):
    """Return two lists of scripts out of the original `scripts` list.

    Scripts that begin with a `start_type` block are returned first. All other
    scripts are returned second.

    """
    match, other = [], []
    for script in scripts:
        if HairballPlugin.script_start_type(script) == start_type:
            match.append(script)
        else:
            other.append(script)
    return match, other


class Initialization(HairballPlugin):

    """Plugin that checks if modified attributes are properly initialized."""

    ATTRIBUTES = ('background', 'costume', 'orientation', 'position', 'size',
                  'visibility')

    STATE_NOT_MODIFIED = 0
    STATE_MODIFIED = 1
    STATE_INITIALIZED = 2

    @classmethod
    def attribute_result(cls, sprites):
        """Return mapping of attributes to if they were initialized or not."""
        retval = dict((x, True) for x in cls.ATTRIBUTES)
        for properties in sprites.values():
            for attribute, state in properties.items():
                retval[attribute] &= state != cls.STATE_MODIFIED
        return retval

    @classmethod
    def attribute_state(cls, partition, attribute):
        """Return the state of the partition for the given attribute.

        If there is more than one `when green flag clicked` script and they
        both modify the attribute, then the attribute is considered to not be
        initialized.

        """
        block_set = cls.BLOCKMAPPING[attribute]
        state = cls.STATE_NOT_MODIFIED
        # TODO: Any regular broadcast blocks encountered in the initialization
        # zone should be added to this loop for conflict checking.
        for script in partition[0]:
            in_zone = True
            for name, level, _ in cls.iter_blocks(script.blocks):
                if name == 'broadcast %e and wait':
                    # TODO: Follow the broadcast and wait scripts that occur in
                    # the initialization zone
                    in_zone = False
                if (name, 'absolute') in block_set:
                    if in_zone and level == 0:  # Success!
                        if state == cls.STATE_NOT_MODIFIED:
                            state = cls.STATE_INITIALIZED
                        else:  # Multiple when green flag clicked conflict
                            state = cls.STATE_MODIFIED
                    elif in_zone:
                        continue  # Conservative ignore for nested absolutes
                    else:
                        state = cls.STATE_MODIFIED
                    break  # The state of the script has been determined
                elif (name, 'relative') in block_set:
                    state = cls.STATE_MODIFIED
                    break
        if state != cls.STATE_NOT_MODIFIED:
            return state
        # Check the other scripts to see if the attribute was ever modified
        for script in partition[1]:
            for name, _, _ in cls.iter_blocks(script.blocks):
                if name in [x[0] for x in block_set]:
                    return cls.STATE_MODIFIED
        return cls.STATE_NOT_MODIFIED

    @classmethod
    def output_results(cls, sprites):
        """Output whether or not each attribute was correctly initialized.

        Attributes that were not modified at all are considered to be properly
        initialized.

        """
        print(' '.join(cls.ATTRIBUTES))
        format_strs = ['{{{0}!s:^{1}}}'.format(x, len(x)) for x in
                       cls.ATTRIBUTES]
        print(' '.join(format_strs).format(**cls.attribute_result(sprites)))

    @classmethod
    def sprite_changes(cls, sprite):
        """Return a mapping of attributes to their initilization state."""
        partition = partition_scripts(sprite.scripts, cls.HAT_GREEN_FLAG)
        retval = dict((x, cls.attribute_state(partition, x)) for x in
                      (x for x in cls.ATTRIBUTES if x != 'background'))
        return retval

    def analyze(self, scratch):
        """Run and return the results of the initial state plugin."""
        changes = dict((x.name, self.sprite_changes(x)) for x in
                       scratch.stage.sprites)
        partition = partition_scripts(scratch.stage.scripts,
                                      self.HAT_GREEN_FLAG)
        changes['stage'] = {'background': self.attribute_state(partition,
                                                               'costume')}
        self.output_results(changes)
        return {'initialized': changes}


class Variables(HairballPlugin):
    """Variable change and initialization

    Checks if variables were changed and if so, if they were initialized.
    """
    def local_vars(self, sprite):
        green_flag, other = partition_scripts(sprite.scripts,
                                              self.HAT_GREEN_FLAG)
        variables = dict((x, 'unused') for x in sprite.vars)
        bandw = False
        for script in green_flag:
            for name, level, block in self.iter_blocks(script.blocks):
                if name == 'broadcast %e and wait':
                    bandw = True
                if name == 'set %v to %s' and level == 0 and not bandw:
                    if block.args[0] in variables.keys():
                        variables[block.args[0]] = 'set'
                elif name == 'set %v to %s' or name == 'change %v by %n':
                    if (block.args[0], 'unused') in variables.items():
                        variables[block.args[0]] = 'changed'
        for script in other:
            for name, level, block in self.iter_blocks(script.blocks):
                if name == 'set %v to %s' or name == 'change %v by %n':
                    if (block.args[0], 'unused') in variables.items():
                        variables[block.args[0]] = 'changed'
        return variables

    def global_vars(self, scratch):
        bandw = False
        variables = dict((x, 'unchanged') for x in scratch.stage.vars)
        green_flag, other = partition_scripts(self.iter_scripts(scratch),
                                              self.HAT_GREEN_FLAG)
        for script in green_flag:
            for name, level, block in self.iter_blocks(script.blocks):
                if name == 'broadcast %e and wait':
                    bandw = True
                if name == 'set %v to %s' and level == 0 and not bandw:
                    if block.args[0] in variables.keys():
                        variables[block.args[0]] = 'set'
                elif name == 'set %v to %s' or name == 'change %v by %n':
                    if (block.args[0], 'unchanged') in variables.items():
                        variables[block.args[0]] = 'changed'
            bandw = False
        for script in other:
            for name, level, block in self.iter_blocks(script.blocks):
                if name == 'set %v to %s' or name == 'change %v by %n':
                    if (block.args[0], 'unchanged') in variables.items():
                        variables[block.args[0]] = 'changed'
        return variables

    def analyze(self, scratch):
        variables = dict()
        for sprite in scratch.stage.sprites:
            variables[sprite.name] = self.local_vars(sprite)
        variables['global'] = self.global_vars(scratch)
        return {'variables': variables}
