#!/usr/bin/env python3

import logging
import os
import shutil
import sys
import unittest

logger = logging.getLogger(__name__)

def runtests(suite, verbosity=1, failfast=False):
    runner = unittest.TextTestRunner(verbosity=verbosity, failfast=failfast)
    results = runner.run(suite)
    return results.failures, results.errors

def collect_tests(args):
    suite = unittest.TestSuite()

    if not args:
        import tests
        module_suite = unittest.TestLoader().loadTestsFromModule(tests)
        suite.addTest(module_suite)
    else:
        cleaned = ['tests.%s' % arg if not arg.startswith('tests.') else arg
                   for arg in args]
        user_suite = unittest.TestLoader().loadTestsFromNames(cleaned)
        suite.addTest(user_suite)

    return suite

if __name__ == '__main__':
    suite = collect_tests(None)
    failures, errors = runtests(suite)

    files_to_delete = [
        'peewee_test.db',
        'peewee_test',
        'tmp.db',
        'peewee_test.bdb.db',
        'peewee_test.cipher.db']
    paths_to_delete = ['peewee_test.bdb.db-journal']
    for filename in files_to_delete:
        if os.path.exists(filename):
            os.unlink(filename)
    for path in paths_to_delete:
        if os.path.exists(path):
            shutil.rmtree(path)

    if errors:
        sys.exit(2)
    elif failures:
        sys.exit(1)

    sys.exit(0)
