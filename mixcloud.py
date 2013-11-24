import collections
import requests


class Mixcloud(object):

    def __init__(self, api_root='https://api.mixcloud.com'):
        self.api_root = api_root

    def artist(self, key):
        url = '{root}/artist/{key}'.format(root=self.api_root, key=key)
        r = requests.get(url)
        return Artist.from_json(r.json())

    def user(self, key):
        url = '{root}/user/{user}'.format(root=self.api_root, user=key)
        r = requests.get(url)
        data = r.json()
        name = data['name']
        return User.from_json(data, m=self)


class Artist(collections.namedtuple('_Artist', 'key name')):

    @staticmethod
    def from_json(data):
        return Artist(data['slug'], data['name'])


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


class Cloudcast(collections.namedtuple('_Cloudcast', 'key name sections')):

    @staticmethod
    def from_json(d):
        sections = [Section.from_json(s) for s in d['sections']]
        return Cloudcast(d['slug'], d['name'], sections)


class Section(collections.namedtuple('_Section', 'start_time')):

    @staticmethod
    def from_json(d):
        return Section(d['start_time'])
