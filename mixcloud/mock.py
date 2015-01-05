import datetime
import httpretty
import json
import mixcloud
import urlparse


class MockServer:

    def __init__(self, api_root=None):
        if api_root is None:
            api_root = 'https://api.mixcloud.com'
        self.api_root = api_root

    def i_am(self, user):
        assert httpretty.is_enabled()
        target_url = '{root}/{key}'.format(root=self.api_root, key=user.key)
        self.register_user(user)
        httpretty.register_uri(httpretty.GET,
                               '{root}/me/'.format(root=self.api_root),
                               status=302,
                               location=target_url)

    def register_artist(self, artist):
        assert httpretty.is_enabled()
        url = '{root}/artist/{key}'.format(root=self.api_root, key=artist.key)
        data = {'slug': artist.key,
                'name': artist.name,
                }
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    def register_user(self, user):
        assert httpretty.is_enabled()
        url = '{root}/{key}'.format(root=self.api_root, key=user.key)
        data = {'username': user.key,
                'name': user.name,
                }
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    def _register_cloudcast_only(self, user, cloudcast):
        assert httpretty.is_enabled()
        self.register_user(user)
        url = '{root}/{user}/{key}'.format(root=self.api_root,
                                           user=user.key,
                                           key=cloudcast.key)
        cc_data = {'slug': cloudcast.key,
                   'name': cloudcast.name,
                   'sections':
                   [{'start_time': s.start_time,
                     'track':
                     {'name': s.track.name,
                      'artist':
                      {'slug': s.track.artist.key,
                       'name': s.track.artist.name,
                       },
                      },
                     }
                    for s in cloudcast.sections()],
                   'tags': [{'name': t}
                            for t in cloudcast.tags],
                   'description': cloudcast.description(),
                   'user': {'username': user.key,
                            'name': user.name,
                            },
                   'created_time': cloudcast.created_time.isoformat(),
                   }
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(cc_data))
        return cc_data

    def _register_cloudcast_list(self, user, cloudcasts):
        assert httpretty.is_enabled()
        url = '{root}/{user}/cloudcasts/'.format(root=self.api_root,
                                                 user=user.key)

        def make_cc_data(cc):
            keys_ok = ['tags', 'name', 'slug', 'user', 'created_time']
            return {k: cc[k] for k in keys_ok}

        def cloudcast_list(method, uri, headers):
            query_string = urlparse.urlparse(uri).query
            query_params = urlparse.parse_qs(query_string)
            limit = None
            offset = None
            if 'limit' in query_params:
                limit = int(query_params['limit'][-1])
            if 'offset' in query_params:
                offset = int(query_params['offset'][-1])

            data = [make_cc_data(cc) for cc in cloudcasts]
            if offset is not None:
                data = data[offset:]
            if limit is not None:
                data = data[:limit]
            body = json.dumps({'data': data})
            return (200, headers, body)

        httpretty.register_uri(httpretty.GET, url, body=cloudcast_list)

    def register_cloudcast(self, user, cloudcast):
        self.register_cloudcasts(user, [cloudcast])

    def register_cloudcasts(self, user, cloudcasts):
        assert httpretty.is_enabled()
        cc_data_list = []
        for cloudcast in cloudcasts:
            cc_data = self._register_cloudcast_only(user, cloudcast)
            cc_data_list.append(cc_data)
        self._register_cloudcast_list(user, cc_data_list)

    def handle_upload(self, upload_callback):
        assert httpretty.is_enabled()
        httpretty.register_uri(httpretty.POST,
                               '{root}/upload/'.format(root=self.api_root),
                               body=upload_callback
                               )

    def mock_upload(self, user):
        def mock_upload(request, uri, headers):
            data = parse_multipart(request.body)
            name = data['name']
            key = mixcloud.slugify(name)
            sections, tags = parse_headers(data)
            description = data['description']
            created_time = datetime.datetime.now()
            cc = mixcloud.Cloudcast(key, name, sections, tags,
                                    description, user, created_time)
            self.register_cloudcast(user, cc)
            return (200, headers, '{}')
        self.handle_upload(mock_upload)


def parse_multipart(d):
    lines = d.split('\n')
    k = None
    v = None
    res = {}
    for l in lines:
        l = l.strip()
        if l.startswith('Content-Disposition'):
            parts = l.split('"')
            k = parts[1]
        elif l.startswith('--'):
            pass
        elif l == '':
            pass
        else:
            v = l
            if k is not None and v is not None:
                res[k] = v
    return res


def listify(d):
    l = [None] * len(d)
    for k, v in d.iteritems():
        l[k] = v
    return l


def make_section(s):
    artist_name = s['artist']
    slug = mixcloud.slugify(artist_name)
    artist = mixcloud.Artist(slug, artist_name)
    track = mixcloud.Track(s['song'], artist)
    sec = mixcloud.Section(int(s['start_time']), track)
    return sec


def parse_headers(data):
    sections = {}
    tags = {}
    for k, v in data.iteritems():
        if k.startswith('sections-'):
            parts = k.split('-')
            secnum = int(parts[1])
            what = parts[2]
            if secnum not in sections:
                sections[secnum] = {}
            sections[secnum][what] = v
        if k.startswith('tags-'):
            parts = k.split('-')
            tagnum = int(parts[1])
            tags[tagnum] = v

    seclist = [make_section(s) for s in listify(sections)]
    taglist = listify(tags)
    return seclist, taglist
