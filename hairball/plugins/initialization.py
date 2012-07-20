from . import PluginController, PluginView, PluginWrapper


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


class Initialization(PluginController):
    """Change and initialization

    Checks if properties were changed and if so, if they were initialized.
    """
    def gen_change(self, sprite, property):
        greenflag = False
        bandw = False
        for script in sprite.scripts:
            if self.hat_type(script) == "When green flag clicked":
                greenflag = True
            else:
                greenflag = False
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
            if self.hat_type(script) == "When green flag clicked":
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
            if self.hat_type(script) == "When green flag clicked":
                for name, level, block in self.block_iter(script):
                    if name == 'doBroadcastAndWait':
                        bandw = True
                    if name == "show" or name == "hide":
                        if level == 0 and not bandw:
                            changed, initialized = True, True
                            return (changed, initialized)
                        else:
                            changed = True
        return (changed, initialized)

    def sprite_changes(self, sprite, global_variables):
        sprite_attr = dict()
        general = ["position", "orientation", "costume", "size"]
        for property in general:
            sprite_attr[property] = self.gen_change(
                sprite, self.BLOCKMAPPING[property])
        sprite_attr["visibility"] = self.visibility_change(sprite)
        var_changes, global_variables = self.variable_change(
            sprite, global_variables)
        sprite_attr["variables"] = var_changes
        return sprite_attr, global_variables

    @PluginWrapper(html=InitializationView)
    def analyze(self, scratch):
        attribute_changes = dict()
        global_vars = dict()
        for key in scratch.stage.vars.keys():
            global_vars[key] = "uninitialized"
        for sprite in scratch.stage.sprites:
            sprite_attr, global_variables = self.sprite_changes(
                sprite, global_vars)
            attribute_changes[sprite.name] = sprite_attr
        stage_changes = dict()
        stage_changes["background"] = self.gen_change(
            scratch.stage, self.BLOCKMAPPING["costume"])
        # check global/stage variables
        # right now we're not looking at what the stage changes
        var_change, global_vars = self.variable_change(
            scratch.stage, global_vars)
        if "changed" in global_vars.values():
            global_change = (True, False)
        elif "set" in global_vars.values():
            global_change = (True, True)
        else:
            global_change = (False, False)
        stage_changes["global variables"] = global_change
        attribute_changes["stage"] = stage_changes
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


class Variables(PluginController):
    """Variable change and initialization

    Checks if variables were changed and if so, if they were initialized.
    """
    def local_vars(self, sprite):
        (greenflag, other) = self.pull_hat(
            "When green flag clicked", list(sprite.scripts))
        variables = dict()
        bandw = False
        for var in sprite.vars.keys():
            variables[var] = "unused"
        for script in greenflag:
            for name, level, block in self.block_iter(script.blocks):
                if name == 'doBroadcastAndWait':
                    bandw = True
                if name == 'setVariable' and level == 0 and not bandw:
                    if block.args[0] in variables.keys():
                        variables[block.args[0]] = 'set'
                elif name == 'setVariable' or name == 'changeVariable':
                    if (block.args[0], "unused") in variables.items():
                        variables[block.args[0]] = "changed"
        for script in other:
            for name, level, block in self.block_iter(script.blocks):
                if name == 'setVariable' or name == 'changeVariable':
                    if (block.args[0], "unused") in variables.items():
                        variables[block.args[0]] = "changed"
        return variables

    def global_vars(self, scratch):
        bandw = False
        variables = dict()
        for key in scratch.stage.vars.keys():
            variables[key] = "unused"
        greenflag = []
        other = []
        for sprite in scratch.stage.sprites:
            (gf, o) = self.pull_hat(
                "When green flag clicked", list(sprite.scripts))
            greenflag.extend(gf)
            other.extend(o)
        if len(scratch.stage.scripts) != 0:
            (gf, o) = self.pull_hat(
                "When green flag clicked", list(scratch.stage.scripts))
            greenflag.extend(gf)
            other.extend(o)
        for script in greenflag:
            for name, level, block in self.block_iter(script.blocks):
                if name == 'doBroadcastAndWait':
                    bandw = True
                if name == 'setVariable' and level == 0 and not bandw:
                    if block.args[0] in variables.keys():
                        variables[block.args[0]] = 'set'
                elif name == 'setVariable' or name == 'changeVariable':
                    if (block.args[0], "unused") in variables.items():
                        variables[block.args[0]] = "changed"
            bandw = False
        for script in other:
            for name, level, block in self.block_iter(script.blocks):
                if name == 'setVariable' or name == 'changeVariable':
                    if (block.args[0], "unused") in variables.items():
                        variables[block.args[0]] = "changed"
        return variables

    @PluginWrapper(html=VariablesView)
    def analyze(self, scratch):
        variables = dict()
        for sprite in scratch.stage.sprites:
            variables[sprite.name] = self.local_vars(sprite)
        variables["global"] = self.global_vars(scratch)
        return self.view_data(variables=variables)
