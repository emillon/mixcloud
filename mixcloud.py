import requests


class Mixcloud(object):

    def __init__(self, api_root='https://api.mixcloud.com'):
        self.api_root = api_root

    def artist(self, name):
        url = '{root}/artist/{artist}'.format(root=self.api_root, artist=name)
        r = requests.get(url)
        data = r.json()
        name = data['name']
        return Artist(name)

    def user(self, name):
        url = '{root}/user/{user}'.format(root=self.api_root, user=name)
        r = requests.get(url)
        data = r.json()
        name = data['name']
        return User(name)


class Artist(object):

    def __init__(self, name):
        self.name = name


class User(object):

    def __init__(self, name):
        self.name = name
