#!/usr/bin/env python3

import os
import pylint.lint

script_dir = os.path.dirname(os.path.realpath(__file__))
run_dir, package_name = os.path.split(script_dir)

os.chdir(run_dir)

pylint_opts = ['--rcfile=%s' % os.path.join(script_dir, 'lint.rc')]
pylint_opts.append(package_name)
pylint.lint.Run(pylint_opts)
