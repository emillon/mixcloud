import collections
import dateutil.parser
import netrc
import re
import requests
import unidecode
import yaml

try:
    from urllib import urlencode
except ImportError:
    # Python 2 fallback.
    from urllib.parse import urlencode


NETRC_MACHINE = 'mixcloud-api'
API_ROOT = 'https://api.mixcloud.com'
OAUTH_ROOT = 'https://www.mixcloud.com/oauth'


class MixcloudOauthError(Exception):
    pass


def setup_yaml():
    def construct_yaml_str(self, node):
        # Override the default string handling function
        # to always return unicode objects
        return self.construct_scalar(node)
    tag = u'tag:yaml.org,2002:str'
    yaml.Loader.add_constructor(tag, construct_yaml_str)
    yaml.SafeLoader.add_constructor(tag, construct_yaml_str)


class MixcloudOauth(object):
    """
    Assists in the OAuth dance with Mixcloud to get an access token.
    """

    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri

    def authorize_url(self):
        """
        Return a URL to redirect the user to for OAuth authentication.
        """
        auth_url = OAUTH_ROOT + '/authorize'
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
        }
        return "{}?{}".format(auth_url, urlencode(params))

    def exchange_token(self, code):
        """
        Exchange the authorization code for an access token.
        """
        access_token_url = OAUTH_ROOT + '/access_token'
        params = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'redirect_uri': self.redirect_uri,
            'code': code,
        }
        resp = requests.get(access_token_url, params=params)
        if not resp.ok:
            raise MixcloudOauthError("Could not get access token.")
        return resp.json()['access_token']


class Mixcloud(object):

    def __init__(self, api_root=API_ROOT, access_token=None):
        self.api_root = api_root
        if access_token is None:
            # Attempt netrc lookup.
            netrc_auth = netrc.netrc().authenticators(NETRC_MACHINE)
            if netrc_auth:
                access_token = netrc_auth[2]
        self.access_token = access_token

    def artist(self, key):
        url = '{root}/artist/{key}'.format(root=self.api_root, key=key)
        r = requests.get(url)
        return Artist.from_json(r.json())

    def user(self, key):
        url = '{root}/{user}'.format(root=self.api_root, user=key)
        r = requests.get(url)
        return User.from_json(r.json(), m=self)

    def me(self):
        url = '{root}/me/'.format(root=self.api_root)
        r = requests.get(url, {'access_token': self.access_token})
        return User.from_json(r.json(), m=self)

    def upload(self, cloudcast, mp3file, picturefile=None):
        url = '{root}/upload/'.format(root=self.api_root)
        payload = {'name': cloudcast.name,
                   'percentage_music': 100,
                   'description': cloudcast.description(),
                   }
        for num, sec in enumerate(cloudcast.sections()):
            payload['sections-%d-artist' % num] = sec.track.artist.name
            payload['sections-%d-song' % num] = sec.track.name
            payload['sections-%d-start_time' % num] = sec.start_time

        for num, tag in enumerate(cloudcast.tags):
            payload['tags-%s-tag' % num] = tag

        files = {'mp3': mp3file}
        if picturefile is not None:
            files['picture'] = picturefile

        r = requests.post(url,
                          data=payload,
                          params={'access_token': self.access_token},
                          files=files,
                          )
        return r

    def upload_yml_file(self, ymlfile, mp3file):
        user = self.me()
        cloudcast = Cloudcast.from_yml(ymlfile, user)
        r = self.upload(cloudcast, mp3file)


class Artist(collections.namedtuple('_Artist', 'key name')):

    @staticmethod
    def from_json(data):
        return Artist(data['slug'], data['name'])

    @staticmethod
    def from_yml(artist):
        return Artist(slugify(artist), artist)


class User(object):

    def __init__(self, key, name, m=None):
        self.m = m
        self.key = key
        self.name = name

    @staticmethod
    def from_json(data, m=None):
        return User(data['username'], data['name'], m=m)

    def cloudcast(self, key):
        url = '{root}/{user}/{cc}'.format(root=self.m.api_root,
                                          user=self.key,
                                          cc=key)
        r = requests.get(url)
        data = r.json()
        return Cloudcast.from_json(data)

    def cloudcasts(self, limit=None, offset=None):
        url = '{root}/{user}/cloudcasts/'.format(root=self.m.api_root,
                                                 user=self.key)
        params = {}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        r = requests.get(url, params=params)
        data = r.json()
        return [Cloudcast.from_json(d, m=self.m) for d in data['data']]


class Cloudcast(object):

    def __init__(self, key, name, sections, tags,
                 description, user, created_time, pictures=None, m=None):
        self.key = key
        self.name = name
        self.tags = tags
        self._description = description
        self._sections = sections
        self.user = user
        self.created_time = created_time
        self.m = m
        self.pictures = pictures

    @staticmethod
    def from_json(d, m=None):
        if 'sections' in d:
            sections = Section.list_from_json(d['sections'])
        else:
            sections = None
        desc = d.get('description')
        tags = [t['name'] for t in d['tags']]
        user = User.from_json(d['user'])
        created_time = dateutil.parser.parse(d['created_time'])
        return Cloudcast(d['slug'],
                         d['name'],
                         sections,
                         tags,
                         desc,
                         user,
                         created_time,
                         pictures=d.get('pictures'),
                         m=m,
                         )

    def _load(self):
        url = '{root}/{user}/{cc}'.format(root=self.m.api_root,
                                          user=self.user.key,
                                          cc=self.key)
        r = requests.get(url)
        d = r.json()
        self._sections = Section.list_from_json(d['sections'])
        self._description = d['description']

    def sections(self):
        """
        Depending on the data available when the instance was created,
        it may be necessary to fetch data.
        """
        if self._sections is None:
            self._load()
        return self._sections

    def description(self):
        """
        May hit server. See Cloudcast.sections
        """
        if self._description is None:
            self._load()
        return self._description

    def picture(self):
        return self.pictures['large']

    @staticmethod
    def from_yml(f, user):
        setup_yaml()
        d = yaml.load(f)
        name = d['title']
        sections = [Section.from_yml(s) for s in d['tracks']]
        key = slugify(name)
        tags = d['tags']
        description = d['desc']
        created_time = None
        c = Cloudcast(key, name, sections, tags, description,
                      user, created_time)
        return c


class Section(collections.namedtuple('_Section', 'start_time track')):

    @staticmethod
    def from_json(d):
        return Section(d['start_time'], Track.from_json(d['track']))

    @staticmethod
    def list_from_json(d):
        return [Section.from_json(s) for s in d]

    @staticmethod
    def from_yml(d):
        artist = Artist.from_yml(d['artist'])
        track = d['track']
        return Section(d['start'], Track(track, artist))


class Track(collections.namedtuple('_Track', 'name artist')):

    @staticmethod
    def from_json(d):
        return Track(d['name'], Artist.from_json(d['artist']))


def slugify(s):
    s = unidecode.unidecode(s).lower()
    return re.sub(r'\W+', '-', s)
