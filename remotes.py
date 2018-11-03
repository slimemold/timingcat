import requests

class AuthError(Exception):
    pass

def get_remote_class_list():
    remote_subclass_list = Remote.__subclasses__()

    remote_class_list = []

    for remote_subclass in remote_subclass_list:
        if hasattr(remote_subclass, 'name'):
            remote_class_list.append(remote_subclass)

    return remote_class_list

class Remote():
    def __init__(self, race_table_model):
        self.race_table_model = race_table_model

    def connect(self, parent):
        pass

    def disconnect(self, parent):
        pass

    def submit_racer_update(self):
        pass

class SimulatedRemote(Remote):
    name = 'Simulated Remote'

class OnTheDayRemote(Remote):
    name = 'OnTheDay.net Remote'
