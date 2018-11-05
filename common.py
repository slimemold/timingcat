"""Common

This module is a dumping ground for various utilities and constants that can be used throughout
the package.
"""

APPLICATION_NAME = 'SexyThyme'
VERSION = '1.0'

def pretty_list(lst, op='and'):
    """Takes a list of words and returns a comma-separated conjunction (with oxford comma)."""

    # Filter out any None's.
    lst = list(filter(None.__ne__, lst))

    if not lst:
        return ''
    if len(lst) == 1:
        return lst[0]
    if len(lst) == 2:
        return lst[0] + ' ' + op + ' ' + lst[1]

    return ', '.join(lst[0:-1]) + ', ' + op + ' ' + lst[-1]

def pluralize(word, count):
    """Takes a word and a count, and returns a phrase. Ex: 18 racers."""
    if count == 0:
        return None

    if count == 1:
        return '%s %s' % (count, word)

    return '%s %s' % (count, word + 's')
