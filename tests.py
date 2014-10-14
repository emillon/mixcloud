import csv
import datetime
import dateutil.tz
import httpretty
import json
import mixcloud
import StringIO
import unittest
from mixcloud.mock import MockServer


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


def make_section(s):
    artist_name = s['artist']
    slug = mixcloud.slugify(artist_name)
    artist = mixcloud.Artist(slug, artist_name)
    track = mixcloud.Track(s['song'], artist)
    sec = mixcloud.Section(int(s['start_time']), track)
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
    taglist = listify(tags)
    return seclist, taglist


def parse_tracklist(s):
    s = s.split('\n')[1:-1]
    reader = csv.reader(s, delimiter='|', quoting=csv.QUOTE_NONE)
    t = [mixcloud.Section(int(l[0]),
                          mixcloud.Track(l[1].strip(),
                                         mixcloud.Artist(None,
                                                         l[2].strip()
                                                         )
                                         )
                          )
         for l in reader]
    return t


afx = mixcloud.Artist('aphex-twin', 'Aphex Twin')
spartacus = mixcloud.User('spartacus', 'Spartacus')
partytime = mixcloud.Cloudcast(
    'party-time', 'Party Time',
    parse_tracklist("""
       0 | Samurai (12" Mix)              | Jazztronik
     416 | Refresher                      | Time of your life
     716 | My time (feat. Crystal Waters) | Dutch
    1061 | Definition of House            | Minimal Funk
    1500 | I dont know                    | Mint Royale
    1763 | Thrill Her                     | Michael Jackson
    2123 | Happy (feat.Charlise)          | Elio Isola
    2442 | Dancin                         | Erick Morillo et al
    2738 | All in my head                 | Kosheen
    """),
    ['Funky house', 'Funk', 'Soul'],
    'Bla bla',
    spartacus,
    datetime.datetime(2009, 8, 2, 16, 55, 1, tzinfo=dateutil.tz.tzutc()),
)
lambiance = mixcloud.Cloudcast(
    'lambiance', "L'ambiance",
    parse_tracklist("""
     10 | As Serious As Your Life                     | Four Tet
     20 | Dynamic Symmetry                            | BT
     30 | Vessel                                      | Jon Hopkins
     40 | Vordhosbn                                   | Aphex Twin
     50 | Colour Eye                                  | Jon Hopkins
     60 | Flite                                       | The Cinematic Orchestra
     70 | Altibzz                                     | Autechre
     80 | Untitled [SAW2 CD1 Track1] (Four Tet remix) | Aphex Twin
     90 | Angelica                                    | Lamb
    100 | Quixotic                                    | Spartacus
    110 | Monday - Paracetamol                        | Ulrich Schnauss
    120 | Aquarius                                    | Boards of Canada
    130 | Channel 1 Suite                             | The Cinematic Orchestra
    """),
    ['Idm', 'Originals', 'Ambient'],
    'Bla bla bla',
    spartacus,
    datetime.datetime(2010, 3, 11, 21, 53, 8, tzinfo=dateutil.tz.tzutc()),
)


class TestMixcloud(unittest.TestCase):

    def setUp(self):
        self.m = mixcloud.Mixcloud()
        httpretty.reset()
        httpretty.enable()
        self.mc = MockServer()

    def tearDown(self):
        httpretty.disable()

    def testArtist(self):
        self.mc.register_artist(afx)
        resp = self.m.artist('aphex-twin')
        self.assertEqual(resp.name, 'Aphex Twin')

    def testUser(self):
        self.mc.register_user(spartacus)
        resp = self.m.user('spartacus')
        self.assertEqual(resp.name, 'Spartacus')

    def testCloudcast(self):
        self.mc.register_cloudcast(spartacus, partytime)
        resp = self.m.user('spartacus')
        cc = resp.cloudcast('party-time')
        self.assertEqual(cc.name, 'Party Time')
        secs = cc.sections()
        self.assertEqual(len(secs), 9)
        sec = secs[1]
        self.assertEqual(sec.start_time, 416)
        self.assertEqual(sec.track.name, 'Refresher')
        self.assertEqual(sec.track.artist.name, 'Time of your life')
        self.assertItemsEqual(cc.tags, ['Funky house', 'Funk', 'Soul'])
        self.assertEqual(cc.description(), 'Bla bla')
        self.assertEqual(cc.user.key, 'spartacus')
        self.assertEqual(cc.user.name, 'Spartacus')

    def testCloudcasts(self):
        self.mc.register_cloudcast(spartacus, partytime)
        resp = self.m.user('spartacus')
        ccs = resp.cloudcasts()
        self.assertEqual(len(ccs), 1)
        cc = ccs[0]
        self.assertEqual(cc.name, 'Party Time')

    def testLogin(self):
        self.mc.i_am(spartacus)
        user = self.m.me()
        self.assertEqual(user.key, spartacus.key)
        self.assertEqual(user.name, spartacus.name)

    def testUpload(self):
        self.mc.i_am(spartacus)

        def upload_callback(request, uri, headers):
            data = parse_multipart(request.body)
            self.assertIn('mp3', data)
            name = data['name']
            key = mixcloud.slugify(name)
            sections, tags = parse_headers(data)
            description = data['description']
            me = self.m.me()
            created_time = datetime.datetime.now()
            cc = mixcloud.Cloudcast(key, name, sections, tags,
                                    description, me, created_time)
            self.mc.register_cloudcast(me, cc)
            return (200, headers, '{}')

        self.mc.handle_upload(upload_callback)
        mp3file = StringIO.StringIO('\x00' * 30)
        r = self.m.upload(partytime, mp3file)
        self.assertEqual(r.status_code, 200)
        me = self.m.me()
        cc = me.cloudcast('party-time')
        self.assertEqual(cc.name, 'Party Time')
        secs = cc.sections()
        self.assertEqual(len(secs), 9)
        sec = secs[3]
        self.assertEqual(sec.start_time, 1061)
        self.assertEqual(sec.track.name, 'Definition of House')
        self.assertEqual(sec.track.artist.name, 'Minimal Funk')
        self.assertItemsEqual(cc.tags, ['Funky house', 'Funk', 'Soul'])
        self.assertEqual(cc.description(), 'Bla bla')

    def testCloudcastsSection(self):
        self.mc.register_cloudcast(spartacus, partytime)
        u = self.m.user('spartacus')
        ccs = u.cloudcasts()
        cc = ccs[0]
        secs = cc.sections()
        self.assertEqual(secs[7].track.name, 'Dancin')

    def testCloudcastsDescription(self):
        self.mc.register_cloudcast(spartacus, partytime)
        u = self.m.user('spartacus')
        ccs = u.cloudcasts()
        cc = ccs[0]
        self.assertEqual(cc.description(), 'Bla bla')

    def testLimit(self):
        self.mc.register_cloudcasts(spartacus, [partytime, lambiance])
        u = self.m.user('spartacus')
        ccs = u.cloudcasts()
        self.assertEqual(len(ccs), 2)
        ccs = u.cloudcasts(limit=1)
        self.assertEqual(len(ccs), 1)
        self.assertEqual(ccs[0].key, 'party-time')
        ccs = u.cloudcasts(offset=1)
        self.assertEqual(len(ccs), 1)
        self.assertEqual(ccs[0].key, 'lambiance')
