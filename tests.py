import httpretty
import json
import mixcloud
import unittest


class TestMixcloud(unittest.TestCase):

    def _register_artist(self, artist):
        assert httpretty.is_enabled()
        url = 'https://api.mixcloud.com/artist/{key}'.format(key=artist.key)
        data = {'name': artist.name}
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    def _register_user(self, key, name):
        assert httpretty.is_enabled()
        url = 'https://api.mixcloud.com/user/{user}'.format(user=key)
        data = {'name': name}
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    def _register_cloudcast(self, user, username, key, name):
        assert httpretty.is_enabled()
        self._register_user(user, username)
        api_root = 'https://api.mixcloud.com'
        url = '{root}/cloudcast/{user}/{key}'.format(root=api_root,
                                                     user=user,
                                                     key=key)
        data = {'name': name}
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))
        #  Register cloudcast list
        url = '{root}/{user}/cloudcasts/'.format(root=api_root, user=user)
        data = {'data': [{'slug': key,
                          'name': name,
                          }
                         ]
                }
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    def setUp(self):
        self.m = mixcloud.Mixcloud()

    @httpretty.activate
    def testArtist(self):
        afx = mixcloud.Artist('aphex-twin', 'Aphex Twin')
        self._register_artist(afx)
        resp = self.m.artist('aphex-twin')
        self.assertEqual(resp.name, 'Aphex Twin')

    @httpretty.activate
    def testUser(self):
        self._register_user('spartacus', 'Spartacus')
        sp = self.m.user('spartacus')
        self.assertEqual(sp.name, 'Spartacus')

    @httpretty.activate
    def testCloudcast(self):
        self._register_cloudcast('spartacus', 'Spartacus',
                                 'party-time', 'Party Time')
        sp = self.m.user('spartacus')
        cc = sp.cloudcast('party-time')
        self.assertEqual(cc.name, 'Party Time')

    @httpretty.activate
    def testCloudcasts(self):
        self._register_cloudcast('spartacus', 'Spartacus',
                                 'party-time', 'Party Time')
        sp = self.m.user('spartacus')
        ccs = sp.cloudcasts()
        self.assertEqual(len(ccs), 1)
        cc = ccs[0]
        self.assertEqual(cc.name, 'Party Time')
