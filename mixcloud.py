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
        return User(key, name, m=self)


class Artist(object):

    def __init__(self, key, name):
        self.key = key
        self.name = name


class User(object):

    def __init__(self, key, name, m=None):
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
        sections = [Section(d['start_time']) for d in data['sections']]
        return Cloudcast(key, name, sections)

    def cloudcasts(self):
        url = '{root}/{user}/cloudcasts/'.format(root=self.m.api_root,
                                                 user=self.key)
        r = requests.get(url)
        data = r.json()
        return [Cloudcast(d['slug'], d['name'], d['sections'])
                for d in data['data']]


class Cloudcast(object):

    def __init__(self, key, name, sections):
        self.key = key
        self.name = name
        self.sections = sections


class Section(object):

    def __init__(self, start_time):
        self.start_time = start_time
