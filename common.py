APPLICATION_NAME = 'SexyThyme'
VERSION = '1.0'

def pretty_list(lst, op='and'):
    # Filter out any None's.
    lst = list(filter(None.__ne__, lst))

    if len(lst) == 0:
        return ''
    if len(lst) == 1:
        return lst[0]
    if len(lst) == 2:
        return lst[0] + ' ' + op + ' ' + lst[1]

    return ', '.join(lst[0:-1]) + ', ' + op + ' ' + lst[-1]

def pluralize(word, count):
    if count == 0:
        return None

    if count == 1:
        return '%s %s' % (count, word)

    return '%s %s' % (count, word + 's')
