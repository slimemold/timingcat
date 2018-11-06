#!/usr/bin/env python3

"""Linting helper script

This is just a wrapper for launching pylint on this package.
"""

import os
import pylint.lint

def main():
    """The main() function just runs pylint."""
    script_dir = os.path.dirname(os.path.realpath(__file__))
    run_dir, package_name = os.path.split(script_dir)

    os.chdir(run_dir)

    pylint_opts = []
    pylint_opts.append(package_name)
    pylint.lint.Run(pylint_opts)

if __name__ == '__main__':
    main()
