import csv
import httpretty
import json
import mixcloud
import re
import StringIO
import unidecode
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

    def _handle_upload(self):
        assert httpretty.is_enabled()

        def make_section(s):
            artist_name = s['artist'][0]
            slug = slugify(artist_name)
            artist = mixcloud.Artist(slug, artist_name)
            track = mixcloud.Track(s['song'][0], artist)
            sec = mixcloud.Section(int(s['start_time'][0]), track)
            return sec

        def listify(d):
            l = [None] * len(d)
            for k, v in d.iteritems():
                l[k] = v
            return l

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
            taglist = [s[0] for s in listify(tags)]
            return seclist, taglist

        def slugify(s):
            s = unidecode.unidecode(s).lower()
            return re.sub(r'\W+', '-', s)

        def upload_callback(request, uri, headers):
            data = request.parsed_body
            self.assertIn('mp3', data)
            name = data['name'][0]
            key = slugify(name)
            sections, tags = parse_headers(data)
            cc = mixcloud.Cloudcast(key, name, sections, tags)
            me = self.m.me()
            self._register_cloudcast(me, cc)
            return (200, headers, '{}')
        httpretty.register_uri(httpretty.POST,
                               'https://api.mixcloud.com/upload/',
                               body=upload_callback
                               )

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

    @httpretty.activate
    def testUpload(self):
        self._i_am(spartacus)
        self._handle_upload()
        mp3file = StringIO.StringIO('\x00' * 30)
        self.m.upload(partytime, mp3file)
        me = self.m.me()
        cc = me.cloudcast('party-time')
        self.assertEqual(cc.name, 'Party Time')
        self.assertEqual(len(cc.sections), 9)
        sec = cc.sections[3]
        self.assertEqual(sec.start_time, 1061)
        self.assertEqual(sec.track.name, 'Definition of House')
        self.assertEqual(sec.track.artist.name, 'Minimal Funk')
        self.assertItemsEqual(cc.tags, ['Funky house', 'Funk', 'Soul'])
