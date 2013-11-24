import collections
import requests


class Mixcloud(object):

    def __init__(self, api_root='https://api.mixcloud.com', access_token=None):
        self.api_root = api_root
        self.access_token = access_token

    def artist(self, key):
        url = '{root}/artist/{key}'.format(root=self.api_root, key=key)
        r = requests.get(url)
        return Artist.from_json(r.json())

    def user(self, key):
        url = '{root}/user/{user}'.format(root=self.api_root, user=key)
        r = requests.get(url)
        return User.from_json(r.json(), m=self)

    def me(self):
        url = '{root}/me/'.format(root=self.api_root)
        r = requests.get(url)
        return User.from_json(r.json(), m=self)

    def upload(self, cloudcast, mp3file):
        url = '{root}/upload/'.format(root=self.api_root)
        mp3data = mp3file.read()
        payload = {'mp3': mp3data,
                   'name': cloudcast.name,
                   }
        sec_headers = {}
        for num, sec in enumerate(cloudcast.sections):
            sec_headers['sections-%d-artist' % num] = sec.track.artist.name
            sec_headers['sections-%d-song' % num] = sec.track.name
            sec_headers['sections-%d-start_time' % num] = sec.start_time

        payload.update(sec_headers)
        r = requests.post(url,
                          data=payload,
                          params={'access_token': self.access_token},
                          )


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


class Cloudcast(collections.namedtuple('_Cloudcast',
                                       'key name sections tags')):

    @staticmethod
    def from_json(d):
        sections = [Section.from_json(s) for s in d['sections']]
        tags = [t['name'] for t in d['tags']]
        return Cloudcast(d['slug'], d['name'], sections, tags)


class Section(collections.namedtuple('_Section', 'start_time track')):

    @staticmethod
    def from_json(d):
        return Section(d['start_time'], Track.from_json(d['track']))


class Track(collections.namedtuple('_Track', 'name artist')):

    @staticmethod
    def from_json(d):
        return Track(d['name'], Artist.from_json(d['artist']))
