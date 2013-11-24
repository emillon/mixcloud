import csv
import httpretty
import json
import mixcloud
import unittest


afx = mixcloud.Artist('aphex-twin', 'Aphex Twin')
spartacus = mixcloud.User('spartacus', 'Spartacus')
pt_data = """
   0 | Samurai (12" Mix)              | Jazztronik
 416 | Refresher                      | Time of your life
 716 | My time (feat. Crystal Waters) | Dutch
1061 | Definition of House            | Minimal Funk
1500 | I dont know                    | Mint Royale
1763 | Thrill Her                     | Michael Jackson
2123 | Happy (feat.Charlise)          | Elio Isola
2442 | Dancin                         | Erick Morillo et al
2738 | All in my head                 | Kosheen
     """.split('\n')[1:-1]
partytime = mixcloud.Cloudcast(
    'party-time', 'Party Time',
    [mixcloud.Section(int(l[0]),
                      mixcloud.Track(l[1].strip(),
                                     mixcloud.Artist(None,
                                                     l[2].strip()
                                                     )
                                     )
                      )
     for l in csv.reader(pt_data, delimiter='|', quoting=csv.QUOTE_NONE)],
    ['Funky house', 'Funk', 'Soul'],
)


class TestMixcloud(unittest.TestCase):

    def _register_artist(self, artist):
        assert httpretty.is_enabled()
        url = 'https://api.mixcloud.com/artist/{key}'.format(key=artist.key)
        data = {'slug': artist.key,
                'name': artist.name,
                }
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
                    for s in cloudcast.sections],
                   'tags': [{'name': t}
                            for t in cloudcast.tags],
                   }
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(cc_data))
        #  Register cloudcast list
        url = '{root}/{user}/cloudcasts/'.format(root=api_root, user=user.key)
        data = {'data': [cc_data]}
        httpretty.register_uri(httpretty.GET, url, body=json.dumps(data))

    def _i_am(self, user):
        assert httpretty.is_enabled()
        target_url = 'https://api.mixcloud.com/user/{key}'.format(key=user.key)
        self._register_user(user)
        httpretty.register_uri(httpretty.GET,
                               'https://api.mixcloud.com/me/',
                               status=302,
                               location=target_url)

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
        self.assertEqual(sec.track.name, 'Refresher')
        self.assertEqual(sec.track.artist.name, 'Time of your life')
        self.assertItemsEqual(cc.tags, ['Funky house', 'Funk', 'Soul'])

    @httpretty.activate
    def testCloudcasts(self):
        self._register_cloudcast(spartacus, partytime)
        resp = self.m.user('spartacus')
        ccs = resp.cloudcasts()
        self.assertEqual(len(ccs), 1)
        cc = ccs[0]
        self.assertEqual(cc.name, 'Party Time')

    @httpretty.activate
    def testLogin(self):
        self._i_am(spartacus)
        user = self.m.me()
        self.assertEqual(user.key, spartacus.key)
        self.assertEqual(user.name, spartacus.name)
