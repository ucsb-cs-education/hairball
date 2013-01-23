from collections import Counter
import copy
from . import HairballPlugin


class BlockTypes(HairballPlugin):
    """Block Types

    Produces a count of each type of block contained in a scratch file.
    """
    def analyze(self, scratch):
        blocks = Counter()
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            for name, level, block in self.iter_blocks(script.blocks):
                blocks.update({name: 1})
        return {'types': blocks.most_common()}


class BlockTotals(HairballPlugin):
    """Block Totals

    Produces a count of each type of block contained in all the scratch files.
    """
    def __init__(self):
        super(BlockTotals, self).__init__()
        self.blocks = Counter()

    def finalize(self):
        for name, count in sorted(self.blocks.items(), key=lambda x: x[1]):
            print('{0:3} {1}'.format(count, name))
        print('{0:3} total'.format(sum(self.blocks.values())))

    def analyze(self, scratch):
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            for name, level, block in self.iter_blocks(script.blocks):
                self.blocks.update({name: 1})
        return {'types': self.blocks}


class DeadCode(HairballPlugin):
    """Dead Code

    Shows all of the dead code for each sprite in a scratch file.
    """
    def __init__(self):
        super(DeadCode, self).__init__()
        self.dead = {}

    def finalize(self):
        file = open('deadcode.txt', 'w')
        file.write("activity, pair, variable_event, sprites with dead code\n")
        for ((group, project), (variable_event, sprite_dict)) in\
                self.blocks.items():
            file.write('\n')
            file.write(project)
            file.write(', ')
            file.write(group)
            file.write(', ')
            file.write(variable_event)
            for key in sprite_dict.keys():
                file.write(', ')
                file.write(key)

    def analyze(self, scratch):
        sprites = {}
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        for script in scripts:
            if script.morph.name not in sprites.keys():
                sprites[script.morph.name] = []
            if not script.reachable:
                sprites[script.morph.name].append(script)
        variable_event = True in self.get_broadcast_events(scripts)
        if hasattr(scratch, 'group') and hasattr(scratch, 'project'):
            self.dead[(scratch.group, scratch.project)] = (
                variable_event, copy.deepcopy(sprites))
        return {'deadcode': (variable_event, sprites)}
