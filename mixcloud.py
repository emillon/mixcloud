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
        return User.from_json(data, m=self)


class Artist(object):

    def __init__(self, key, name):
        self.key = key
        self.name = name


class User(object):

    def __init__(self, key, name, m=None):
        self.m = m
        self.key = key
        self.name = name

    @staticmethod
    def from_json(data, m=None):
        return User(data['username'], data['name'], m=m)

    def cloudcast(self, key):
        url = '{root}/cloudcast/{user}/{cc}'.format(root=self.m.api_root,
                                                    user=self.key,
                                                    cc=key)
        r = requests.get(url)
        data = r.json()
        return Cloudcast.from_json(data)

    def cloudcasts(self):
        url = '{root}/{user}/cloudcasts/'.format(root=self.m.api_root,
                                                 user=self.key)
        r = requests.get(url)
        data = r.json()
        return [Cloudcast.from_json(d) for d in data['data']]


class Cloudcast(object):

    def __init__(self, key, name, sections):
        self.key = key
        self.name = name
        self.sections = sections

    @staticmethod
    def from_json(d):
        sections = [Section.from_json(s) for s in d['sections']]
        return Cloudcast(d['slug'], d['name'], sections)


class Section(object):

    def __init__(self, start_time):
        self.start_time = start_time

    @staticmethod
    def from_json(d):
        return Section(d['start_time'])
