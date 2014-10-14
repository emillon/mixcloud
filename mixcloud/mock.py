import datetime
import httpretty
import json
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
