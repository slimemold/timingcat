APPLICATION_NAME = 'SexyThyme'
VERSION = '1.0'

def pretty_list(lst, op='and'):
    if len(lst) == 0:
        return ''
    if len(lst) == 1:
        return lst[0]
    if len(lst) == 2:
        return lst[0] + ' ' + op + ' ' + lst[1]

    return ', '.join(lst[0:-1]) + ', ' + op + ' ' + lst[-1]
