"""A plugin-able framework for the static analysis of Scratch projects."""

from __future__ import print_function
import appdirs
import cPickle
import errno
import importlib
import kurt
import os
import sys
import traceback
from hashlib import sha1
from imp import load_source
from optparse import OptionParser
from .plugins import HairballPlugin


__version__ = '0.2rc1'


class KurtCache(object):

    """Interface to an on-disk cache of processed Kurt objects."""

    DEFAULT_CACHE_DIR = appdirs.user_cache_dir(
        appname='Hairball', appauthor='bboe')

    @staticmethod
    def path_to_key(filepath):
        """Return the sha1sum (key) belonging to the file at filepath."""
        tmp, last = os.path.split(filepath)
        tmp, middle = os.path.split(tmp)
        return '{}{}{}'.format(os.path.basename(tmp), middle,
                               os.path.splitext(last)[0])

    def __init__(self, cache_dir=DEFAULT_CACHE_DIR):
        """Initialize the index of cached files."""
        # Create the cache directory
        try:
            os.makedirs(cache_dir)
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise  # Don't continue without cache support
        self.hashes = set()
        self.cache_dir = cache_dir
        # Initialize the index
        for path, _, filenames in os.walk(cache_dir):
            for filename in filenames:
                if filename.endswith('.pkl'):
                    filepath = os.path.join(path, filename)
                    self.hashes.add(self.path_to_key(filepath))

    def key_to_path(self, key):
        """Return the fullpath to the file with sha1sum key."""
        return os.path.join(self.cache_dir, key[:2], key[2:4],
                            key[4:] + '.pkl')

    def load(self, filename):
        """Optimized load and return the parsed version of filename.

        Uses the on-disk parse cache if the file is located in it.

        """
        # Compute sha1 hash (key)
        with open(filename) as fp:
            key = sha1(fp.read()).hexdigest()
        path = self.key_to_path(key)
        # Return the cached file if available
        if key in self.hashes:
            with open(path) as fp:
                return cPickle.load(fp)
        # Create the nested cache directory
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
        # Process the file and save in the cache
        scratch = kurt.Project.load(filename)
        with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT,
                               0400), 'w') as fp:
            # open file for writing but make it immediately read-only
            cPickle.dump(scratch, fp, cPickle.HIGHEST_PROTOCOL)
        self.hashes.add(key)
        return scratch


class Hairball(object):

    """The Hairball exeuction class.

    This class is responsible for parsing command line arguments, loading the
    plugins, and running the plugins on the specified scratch files.

    """

    def __init__(self, options, paths, cache=True):
        """Initialize a Hairball instance."""
        self.options = options
        self.paths = paths

        if options.kurt_plugin:
            for kurt_plugin in options.kurt_plugin:
                failure = False
                if kurt_plugin.endswith('.py') and os.path.isfile(kurt_plugin):
                    module = os.path.splitext(os.path.basename(kurt_plugin))[0]
                    try:
                        load_source(module, kurt_plugin)
                    except Exception:  # TODO: Enumerate possible exceptions
                        failure = True
                else:
                    try:
                        importlib.import_module(kurt_plugin)
                    except ImportError:
                        failure = True
                if failure and not options.quiet:
                    print('Could not load Kurt plugin: {}'.format(kurt_plugin))

        # Initialization Data
        if cache is True:
            self.cache = KurtCache()
        elif cache:
            self.cache = cache
        else:
            self.cache = False
        self.plugins = []
        self.extensions = [x.extension for x in
                           kurt.plugin.Kurt.plugins.values()]

    def hairball_files(self, paths, extensions):
        """Yield filepath to files with the proper extension within paths."""
        def add_file(filename):
            return os.path.splitext(filename)[1] in extensions

        while paths:
            arg_path = paths.pop(0)
            if os.path.isdir(arg_path):
                found = False
                for path, dirs, files in os.walk(arg_path):
                    dirs.sort()  # Traverse in sorted order
                    for filename in sorted(files):
                        if add_file(filename):
                            yield os.path.join(path, filename)
                            found = True
                if not found:
                    if not self.options.quiet:
                        print('No files found in {}'.format(arg_path))
            elif add_file(arg_path):
                yield arg_path
            elif not self.options.quiet:
                print('Invalid file {}'.format(arg_path))
                print('Did you forget to load a Kurt plugin (-k)?')

    def finalize(self):
        """Indicate that analysis is complete.

        Calling finalize  will call the finalize method of all plugins thus
        allowing them to output any aggregate results or perform any clean-up.

        """
        for plugin in self.plugins:
            plugin.finalize()

    def initialize_plugins(self):
        """Attempt to Load and initialize all the plugins.

        Any issues loading plugins will be output to stderr.

        """
        for plugin_name in self.options.plugin:
            parts = plugin_name.split('.')
            if len(parts) > 1:
                module_name = '.'.join(parts[:-1])
                class_name = parts[-1]
            else:
                # Use the titlecase format of the module name as the class name
                module_name = parts[0]
                class_name = parts[0].title()

            # First try to load plugins from the passed in plugins_dir and then
            # from the hairball.plugins package.
            plugin = None
            for package in (None, 'hairball.plugins'):
                if package:
                    module_name = '{}.{}'.format(package, module_name)
                try:
                    module = __import__(module_name, fromlist=[class_name])
                    # Initializes the plugin by calling its constructor
                    plugin = getattr(module, class_name)()

                    # Verify plugin is of the correct class
                    if not isinstance(plugin, HairballPlugin):
                        sys.stderr.write('Invalid type for plugin {}: {}\n'
                                         .format(plugin_name, type(plugin)))
                        plugin = None
                    else:
                        break
                except (ImportError, AttributeError):
                    pass
            if plugin:
                self.plugins.append(plugin)
            else:
                sys.stderr.write('Cannot find plugin {}\n'.format(plugin_name))
        if not self.plugins:
            sys.stderr.write('No plugins loaded. Goodbye!\n')
            sys.exit(1)

    def process(self):
        """Run the analysis across all files found in the given paths.

        Each file is loaded once and all plugins are run against it before
        loading the next file.

        """
        for filename in self.hairball_files(self.paths, self.extensions):
            if not self.options.quiet:
                print(filename)
            if self.cache:
                scratch = self.cache.load(filename)
            else:
                try:
                    scratch = kurt.Project.load(filename)
                except Exception:  # pylint: disable=W0703
                    traceback.print_exc()
                    continue
            for plugin in self.plugins:
                # pylint: disable=W0212
                plugin._process(scratch, filename=filename)
                # pylint: enable=W0212


def main():
    """The entrypoint for the hairball command installed via setup.py."""
    description = ('PATH can be either the path to a scratch file, or a '
                   'directory containing scratch files. Multiple PATH '
                   'arguments can be provided.')
    parser = OptionParser(usage='%prog -p PLUGIN_NAME [options] PATH...',
                          description=description,
                          version='%prog {}'.format(__version__))
    parser.add_option('-d', '--plugin-dir', metavar='DIR',
                      help=('Specify the path to a directory containing '
                            'plugins. Plugins in this directory take '
                            'precedence over similarly named plugins '
                            'included with Hairball.'))
    parser.add_option('-p', '--plugin', action='append',
                      help=('Use the named plugin to perform analysis. '
                            'This option can be provided multiple times.'))
    parser.add_option('-k', '--kurt-plugin', action='append',
                      help=('Provide either a python import path (e.g, '
                            'kelp.octopi) to a package/module, or the path'
                            ' to a python file, which will be loaded as a '
                            'Kurt plugin. This option can be provided '
                            'multiple times.'))
    parser.add_option('-q', '--quiet', action='store_true',
                      help=('Prevent output from Hairball. Plugins may still '
                            'produce output.'))
    options, args = parser.parse_args(sys.argv[1:])

    if not options.plugin:
        parser.error('At least one plugin must be specified via -p.')
    if not args:
        parser.error('At least one PATH must be provided.')

    if options.plugin_dir:
        if os.path.isdir(options.plugin_dir):
            sys.path.append(options.plugin_dir)
        else:
            parser.error('{} is not a directory'.format(options.plugin_dir))

    hairball = Hairball(options, args, cache=True)
    hairball.initialize_plugins()
    hairball.process()
    hairball.finalize()
