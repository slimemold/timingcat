import inspect
import requests
import sys

def get_remote_class_list():
    clsmembers = inspect.getmembers(sys.modules[__name__], inspect.isclass)

    remote_classes = []
    for class_name, class_type in [m for m in clsmembers if m[1].__module__ == 'remotes']:
        if hasattr(class_type, 'name'):
            remote_classes.append(class_type)

    return remote_classes

class Remote():
    def connect(self):
        pass

    def disconnect(self):
        pass

    def submit_racer_update(self):
        return NotImplemented

class SimulatedRemote(Remote):
    name = 'Simulated Remote'

class OnTheDayRemote(Remote):
    name = 'OnTheDay.net Remote'
