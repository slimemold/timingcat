import requests

class Remote():
    def authenticate(self):
        return NotImplemented

    def submit_racer_update(self):
        return NotImplemented

class OnTheDayRemote(Remote):
    pass
