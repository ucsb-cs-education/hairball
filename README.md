# Installation for development

## Prerequisites

 * virtualenv

To install `virtualenv` a python package installer is
required. This instruction will use `pip`.

### Ubuntu/debian installation of prerequisites

        sudo apt-get install python-setuptools
        sudo easy_install pip

### Mac OS X installation of prerequisites

        sudo easy_install pip
        sudo pip install virtualenv
        # Follow these instructions for git installation
        # https://help.github.com/articles/set-up-git#platform-mac

## Configure and become familiar with git

Regardless of how you installed git, please follow
[these](https://help.github.com/articles/set-up-git#platform-all) instructions
beginning with the section "Set Up Git" to configure your name and email
combination. Also, if you are not familiar with git, please go through the
[try.github.com](http://try.github.com/) tutorial.

## Check out the project and run in development mode

0. Check out the source

        git clone git@github.com:ucsb-cs-education/hairball.git

0. Create the virtual environment

    These examples use `~/.venv` as the virtual environment location,
    however, feel free to use whatever you prefer.

        virtualenv ~/.venv/hairball

0. Load the virtual environment (Note: you will need to run this everytime you
open a new terminal to run the project's commands)

        source ~/.venv/hairball/bin/activate

0. Install the package and its dependencies in development mode

        cd hairball
        python setup.py develop

# Developing Plugins

## Loading Plugins

The plugins for the web service are stored in the
`hairball/hairball/plugins` folder. The association between projects
and plugins is contained the attribute `plugins` of a project in the
database. See the above section on `Working with the Database` for information
on adding and removing projects. Note that both the webserver processes and the
`process_scratch_files` processes need to be restarted whenever projects are
modified.

## Writing Plugins

A plugin is a python class that inherits from the class
`hairball.plugins.PluginBase` and defines at least a `__init__` function, a
`_process` function and a class doc string (a comment).

The classes that define plugins should be grouped by functionality into a
single python module (`.py` file) and placed in the plugins folder. For
example, a set of plugins dealing with scratch audio might be grouped into
the file `audio.py`. If their class names were `SpriteVolume`, `UniqueBeats`,
and `VolumeReset` then the plugin names would be `audio.SpriteVolume`,
`audio.UniqueBeats` and `audio.VolumeReset` respectively.

A complete example of a simple plugin, referred to as `simple.Simple` (or
shortened as `simple` when the class name is the title-cased version of the
module name) is as follows:

### sample.py

    from . import PluginBase

    class Simple(PluginBase):
        """Produces the standard 'Hello World' message."""

        def __init__(self, batch):
            super(Simple, self).__init__(name='The Simple Plugin', batch=batch)

        def _process(self, scratch):
            return 'Hello World!'

---
