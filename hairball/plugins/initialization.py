from . import HairballPlugin, PluginView, PluginWrapper
import copy


class InitializationView(PluginView):
    def add(self, property, (changed, initialized)):
        attr_changes = "{0} change: {1} <br />".format(property, changed)
        if changed:
            attr_changes += '<span class = "indent1"> Initialized: '
            attr_changes += '{0} </span>'.format(initialized)
            attr_changes += '<br />'
        return attr_changes

    def view(self, data):
        attribute_changes = ""
        for (sprite, properties) in data['initialized'].items():
            attribute_changes += sprite + "<br />"
            for property in properties:
                attribute_changes += self.add(
                    property, data['initialized'][sprite][property])
            attribute_changes += "<br />"
        return '<p>{0}</p>'.format(attribute_changes)


class Initialization(HairballPlugin):
    """Change and initialization

    Checks if properties were changed and if so, if they were initialized.
    """
    def __init__(self):
        super(Initialization, self).__init__()
        self.initialization = {}

    def finalize(self):
        file = open('initialization.txt', 'w')
        file.write("activity, pair: background costume")
        file.write(" orientation position size visibility")
        for ((group, project), sprites) in self.initialization.items():
            file.write('\n{0}, {1}: '.format(project, group))
            properties = self.sort_by_prop(sprites)
            file.write("{0} {1} {2} {3} {4} {5}"
                       .format(properties["background"], properties["costume"],
                               properties["orientation"],
                               properties["position"], properties["size"],
                               properties["visibility"]))

    def sort_by_prop(self, sprites):
        init = {}
        init["costume"] = 1
        init["visibility"] = 1
        init["position"] = 1
        init["orientation"] = 1
        init["size"] = 1
        (changed, initialized) = sprites["stage"]["background"]
        if not changed:
            init["background"] = 1
        elif changed and initialized:
            init["background"] = 1
        else:
            init["background"] = 0
        del sprites["stage"]
        for (sprite, properties) in sprites.items():
            for (property, (changed, initialized)) in properties.items():
                if changed and not initialized:
                    init[property] = 0
        return init

    def gen_change(self, sprite, gf, other, property):
        changed = False
        initialized = False
        bandw = False
        # first check the green flag scripts
        for script in gf:
            bandw = False
            for name, level, block in self.iter_blocks(script.blocks):
                print name
                if name == "broadcast %e and wait":
                    bandw = True
                temp = set([(name, "absolute"),
                            (name, "relative")])
                if temp & property:
                    if (name, "absolute") in property:
                        if not bandw and level == 0:
                            (changed, initialized) = (True, True)
                        elif not initialized:
                            (changed, initialized) = (True, False)
                    elif not initialized:
                        (changed, initialized) = (True, False)
        # now check the others for any change
        for script in other:
            for name, level, block in self.iter_blocks(script.blocks):
                temp = set([(name, "absolute"),
                            (name, "relative")])
                if temp & property and not changed:
                    return (True, False)
        return (changed, initialized)

    def visibility_change(self, sprite, gf, other):
        bandw = False
        changed = False
        initialized = False
        for script in gf:
            bandw = False
            for name, level, block in self.iter_blocks(script):
                if name == "broadcast %e and wait":
                    bandw = True
                if name == "show" or name == "hide":
                    if level == 0 and not bandw:
                        (changed, initialized) = (True, True)
                    elif not initialized:
                        (changed, initialized) = (True, False)
        for script in other:
            for name, level, block in self.iter_blocks(script):
                if name == "show" or name == "hide":
                    if not changed:
                        (changed, initialized) = (True, False)
        return (changed, initialized)

    def sprite_changes(self, sprite):
        sprite_attr = dict()
        general = ["position", "orientation", "costume", "size"]
        (gf, other) = self.pull_hat("when green flag clicked", sprite.scripts)
        print sprite.name, gf
        for property in general:
            sprite_attr[property] = self.gen_change(
                sprite, gf, other, self.BLOCKMAPPING[property])
        sprite_attr["visibility"] = self.visibility_change(sprite, gf, other)
        return sprite_attr

    @PluginWrapper(html=InitializationView)
    def analyze(self, scratch):
        attribute_changes = dict()
        for sprite in scratch.stage.sprites:
            attribute_changes[sprite.name] = self.sprite_changes(sprite)
        attribute_changes["stage"] = {}
        (gf, other) = self.pull_hat("when green flag clicked",
                                    scratch.stage.scripts)
        attribute_changes["stage"]["background"] = self.gen_change(
            scratch.stage, gf, other, self.BLOCKMAPPING["costume"])
        if hasattr(scratch, 'group') and hasattr(scratch, 'project'):
            (group, project) = (scratch.group, scratch.project)
            self.initialization[(group, project)] = copy.deepcopy(
                attribute_changes)
        return self.view_data(initialized=attribute_changes)


class VariablesView(PluginView):
    def view(self, data):
        variables = ""
        for name, vars in data['variables'].items():
            variables += '{0} <br />'.format(name)
            for variable, change in vars.items():
                variables += '{0}: {1} <br />'.format(variable, change)
            variables += '<br />'
        return '<p>{0}</p>'.format(variables)


class Variables(HairballPlugin):
    """Variable change and initialization

    Checks if variables were changed and if so, if they were initialized.
    """
    def local_vars(self, sprite):
        (greenflag, other) = self.pull_hat(
            "when green flag clicked", list(sprite.scripts))
        variables = dict()
        bandw = False
        for var in sprite.vars.keys():
            variables[var] = "unused"
        for script in greenflag:
            for name, level, block in self.iter_blocks(script.blocks):
                if name == "broadcast %e and wait":
                    bandw = True
                if name == "set %v to %s" and level == 0 and not bandw:
                    if block.args[0] in variables.keys():
                        variables[block.args[0]] = 'set'
                elif name == "set %v to %s" or name == "change %v by %n":
                    if (block.args[0], "unused") in variables.items():
                        variables[block.args[0]] = "changed"
        for script in other:
            for name, level, block in self.iter_blocks(script.blocks):
                if name == "set %v to %s" or name == "change %v by %n":
                    if (block.args[0], "unused") in variables.items():
                        variables[block.args[0]] = "changed"
        return variables

    def global_vars(self, scratch):
        bandw = False
        variables = dict()
        for key in scratch.stage.vars.keys():
            variables[key] = "unchanged"
        gf = []
        other = []
        scripts = scratch.stage.scripts[:]
        [scripts.extend(x.scripts) for x in scratch.stage.sprites]
        (gf, other) = self.pull_hat("when green flag clicked", scripts)
        for script in gf:
            for name, level, block in self.iter_blocks(script.blocks):
                if name == "broadcast %e and wait":
                    bandw = True
                if name == "set %v to %s" and level == 0 and not bandw:
                    if block.args[0] in variables.keys():
                        variables[block.args[0]] = 'set'
                elif name == "set %v to %s" or name == "change %v by %n":
                    if (block.args[0], "unchanged") in variables.items():
                        variables[block.args[0]] = "changed"
            bandw = False
        for script in other:
            for name, level, block in self.iter_blocks(script.blocks):
                if name == "set %v to %s" or name == "change %v by %n":
                    if (block.args[0], "unchanged") in variables.items():
                        variables[block.args[0]] = "changed"
        return variables

    @PluginWrapper(html=VariablesView)
    def analyze(self, scratch):
        variables = dict()
        for sprite in scratch.stage.sprites:
            variables[sprite.name] = self.local_vars(sprite)
        variables["global"] = self.global_vars(scratch)
        return self.view_data(variables=variables)
