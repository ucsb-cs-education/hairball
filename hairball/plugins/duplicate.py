"""This module provides plugins for basic duplicate code detection."""

from __future__ import print_function
from hairball.plugins import HairballPlugin


class DuplicateScripts(HairballPlugin):

    """Plugin that detects duplicate scripts within a project."""

    def __init__(self):
        """Initialize an instance of the DuplicateScripts plugin."""
        super(DuplicateScripts, self).__init__()
        self.total_duplicate = 0
        self.list_duplicate = []

    def finalize(self):
        """Output the duplicate scripts detected."""
        if self.total_duplicate > 0:
            print('{} duplicate scripts found'.format(self.total_duplicate))
            for duplicate in self.list_duplicate:
                print(duplicate)

    def analyze(self, scratch, **kwargs):
        """Run and return the results from the DuplicateChecks plugin.

        Only takes into account scripts with more than 3 blocks.

        """
        scripts_set = set()
        for script in self.iter_scripts(scratch):
            blocks_list = []
            for name, _, _ in self.iter_blocks(script.blocks):
                blocks_list.append(name)
            blocks_tuple = tuple(blocks_list)
            if blocks_tuple in scripts_set:
                if len(blocks_list) > 3:
                    self.total_duplicate += 1
                    self.list_duplicate.append(blocks_list)
            else:
                scripts_set.add(blocks_tuple)
