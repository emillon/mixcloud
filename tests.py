import httpretty
import json
import mixcloud
import unittest


afx = mixcloud.Artist('aphex-twin', 'Aphex Twin')
spartacus = mixcloud.User('spartacus', 'Spartacus')
partytime = mixcloud.Cloudcast('party-time', 'Party Time',
                               [mixcloud.Section(0),
                                mixcloud.Section(416),
                                mixcloud.Section(716),
                                mixcloud.Section(1061),
                                mixcloud.Section(1500),
                                mixcloud.Section(1763),
                                mixcloud.Section(2123),
                                mixcloud.Section(2442),
                                mixcloud.Section(2738),
                                ]
                               )


class TestMixcloud(unittest.TestCase):

    def _register_artist(self, artist):
        assert httpretty.is_enabled()
        url = 'https://api.mixcloud.com/artist/{key}'.format(key=artist.key)
        data = {'name': artist.name}
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    def _register_user(self, user):
        assert httpretty.is_enabled()
        url = 'https://api.mixcloud.com/user/{key}'.format(key=user.key)
        data = {'username': user.key,
                'name': user.name,
                }
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    def _register_cloudcast(self, user, cloudcast):
        assert httpretty.is_enabled()
        self._register_user(user)
        api_root = 'https://api.mixcloud.com'
        url = '{root}/cloudcast/{user}/{key}'.format(root=api_root,
                                                     user=user.key,
                                                     key=cloudcast.key)
        cc_data = {'slug': cloudcast.key,
                   'name': cloudcast.name,
                   'sections': [{'start_time': s.start_time}
                                for s in cloudcast.sections],
                   }
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(cc_data))
        #  Register cloudcast list
        url = '{root}/{user}/cloudcasts/'.format(root=api_root, user=user.key)
        data = {'data': [cc_data]}
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    def setUp(self):
        self.m = mixcloud.Mixcloud()

    @httpretty.activate
    def testArtist(self):
        self._register_artist(afx)
        resp = self.m.artist('aphex-twin')
        self.assertEqual(resp.name, 'Aphex Twin')

    @httpretty.activate
    def testUser(self):
        self._register_user(spartacus)
        resp = self.m.user('spartacus')
        self.assertEqual(resp.name, 'Spartacus')

    @httpretty.activate
    def testCloudcast(self):
        self._register_cloudcast(spartacus, partytime)
        resp = self.m.user('spartacus')
        cc = resp.cloudcast('party-time')
        self.assertEqual(cc.name, 'Party Time')
        self.assertEqual(len(cc.sections), 9)
        sec = cc.sections[1]
        self.assertEqual(sec.start_time, 416)

    @httpretty.activate
    def testCloudcasts(self):
        self._register_cloudcast(spartacus, partytime)
        resp = self.m.user('spartacus')
        ccs = resp.cloudcasts()
        self.assertEqual(len(ccs), 1)
        cc = ccs[0]
        self.assertEqual(cc.name, 'Party Time')
