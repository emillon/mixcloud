import requests


class Mixcloud(object):

    def __init__(self, api_root='https://api.mixcloud.com'):
        self.api_root = api_root

    def artist(self, key):
        url = '{root}/artist/{key}'.format(root=self.api_root, key=key)
        r = requests.get(url)
        data = r.json()
        name = data['name']
        return Artist(key, name)

    def user(self, key):
        url = '{root}/user/{user}'.format(root=self.api_root, user=key)
        r = requests.get(url)
        data = r.json()
        name = data['name']
        return User(self, key, name)


class Artist(object):

    def __init__(self, key, name):
        self.key = key
        self.name = name


class User(object):

    def __init__(self, m, key, name):
        self.m = m
        self.key = key
        self.name = name

    def cloudcast(self, key):
        url = '{root}/cloudcast/{user}/{cc}'.format(root=self.m.api_root,
                                                    user=self.key,
                                                    cc=key)
        r = requests.get(url)
        data = r.json()
        name = data['name']
        return Cloudcast(key, name)

    def cloudcasts(self):
        url = '{root}/{user}/cloudcasts/'.format(root=self.m.api_root,
                                                 user=self.key)
        r = requests.get(url)
        data = r.json()
        return [Cloudcast(d['slug'], d['name']) for d in data['data']]


class Cloudcast(object):

    def __init__(self, key, name):
        self.key = key
        self.name = name
