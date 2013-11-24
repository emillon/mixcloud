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

    @httpretty.activate
    def testArtist(self):
        self._register_artist('aphex-twin', 'Aphex Twin')
        m = mixcloud.Mixcloud()
        afx = m.artist('aphex-twin')
        self.assertEqual(afx.name, 'Aphex Twin')
