import httpretty
import json
import mixcloud
import unittest


class TestMixcloud(unittest.TestCase):

    def _register_artist(self, key, name):
        assert httpretty.is_enabled()
        url = 'https://api.mixcloud.com/artist/{artist}'.format(artist=key)
        data = {'name': name}
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    def _register_user(self, key, name):
        assert httpretty.is_enabled()
        url = 'https://api.mixcloud.com/user/{user}'.format(user=key)
        data = {'name': name}
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    @httpretty.activate
    def testArtist(self):
        self._register_artist('aphex-twin', 'Aphex Twin')
        m = mixcloud.Mixcloud()
        afx = m.artist('aphex-twin')
        self.assertEqual(afx.name, 'Aphex Twin')

    @httpretty.activate
    def testUser(self):
        self._register_user('spartacus', 'Spartacus')
        m = mixcloud.Mixcloud()
        sp = m.user('spartacus')
        self.assertEqual(sp.name, 'Spartacus')
