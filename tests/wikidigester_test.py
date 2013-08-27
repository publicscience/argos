import unittest
from digester.wikidigester import WikiDigester
from adipose import Adipose

from time import sleep

class WikiDigesterTest(unittest.TestCase):
    def setUp(self):
        self.w = WikiDigester('tests/data/article.xml', 'pages', db='test')
        self.w.purge()

    def tearDown(self):
        self.w.purge()
        self.w = None

    def test_instance(self):
        self.assertIsInstance(self.w, WikiDigester)

    def test_counts_docs(self):
        self._digest()
        self.assertEqual(self.w.num_docs, 1)

    def test_local_digest(self):
        self._digest()

    def test_distrib_digest(self):
        # Requires that RabbitMQ and a Celery worker are running.
        self.w = WikiDigester('tests/data/article.xml', 'pages', distrib=True, db='test')
        self.w.purge()
        self._digest()

    def test_local_digest_updates(self):
        self._digest_updates()

    def test_distrib_digest_updates(self):
        # Requires that RabbitMQ and a Celery worker are running.
        self.w = WikiDigester('tests/data/article.xml', 'pages', distrib=True, db='test')
        self.w.purge()
        self._digest_updates()

    def test_bag_of_words_retrieval(self):
        self.w = WikiDigester('tests/data/simple_article.xml', 'pages', db='test')
        self.w.purge()
        self.w.digest()

        # Warning: `doc` is a DOOZY
        id = 12
        doc = dict([(354288642, 2), (356254723, 2), (95814148, 1), (44564822, 2), (36962594, 4), (103678476, 1), (98828802, 1), (98894350, 1), (101581328, 1), (107020817, 1), (1334118403, 1), (70713774, 1), (104530454, 1), (610403674, 1), (389284894, 1), (69271984, 2), (375260194, 2), (377226275, 2), (381551652, 2), (107086376, 1), (106365481, 2), (109904426, 1), (108462638, 1), (111673903, 1), (378143793, 4), (381223987, 2), (3473461, 1), (382534710, 1), (3604535, 2), (388039736, 1), (405734495, 1), (70320565, 1), (386729025, 1), (4325442, 2), (4390979, 1), (127468105, 1), (4915275, 1), (371983373, 1), (131924560, 1), (9830499, 1), (130613844, 2), (133169751, 1), (401343576, 1), (9961572, 1), (399836250, 1), (408355932, 1), (137495135, 2), (695338512, 2), (134546018, 1), (41222454, 1), (135397988, 1), (253690726, 1), (6684774, 1), (103481873, 1), (10158184, 1), (307364791, 3), (136512107, 2), (138609261, 1), (142213742, 1), (138084975, 1), (139068016, 2), (141296241, 1), (140837492, 1), (314442686, 1), (144900729, 1), (136970874, 2), (148374140, 2), (148243069, 1), (146408063, 1), (149947008, 2), (453051521, 1), (10289259, 1), (135660138, 1), (13566093, 1), (149750415, 1), (180224707, 1), (435225710, 1), (454165654, 1), (554763545, 1), (22151393, 1), (32374980, 1), (20512924, 1), (43712841, 6), (11075696, 1), (471008418, 1), (133038682, 1), (288949150, 5), (7405681, 1), (470746280, 1), (22282409, 1), (320603079, 1), (250479433, 1), (16253106, 1), (72221104, 1), (173933237, 1), (16908472, 1), (176030395, 1), (32702666, 1), (17629374, 1), (69337494, 1), (175768259, 1), (181535428, 2), (32374981, 1), (34668755, 2), (19792073, 1), (255001435, 1), (348652235, 1), (555877666, 1), (180028109, 1), (179372752, 1), (34668754, 2), (109445667, 2), (20578516, 2), (185729751, 1), (183304920, 1), (35061977, 1), (20971738, 1), (182715087, 1), (190251741, 6), (29294814, 2), (185139935, 1), (34406608, 2), (189072098, 1), (192217827, 1), (34603220, 2), (29098214, 2), (195691240, 1), (190186217, 1), (194249450, 1), (193921772, 3), (34603218, 1), (147260146, 1), (187564787, 2), (528221430, 1), (201130743, 1), (152568481, 1), (143786623, 1), (197591804, 1), (321127375, 1), (199820033, 1), (202441474, 1), (52822280, 1), (549061902, 1), (203424528, 1), (109380142, 1), (553387286, 1), (223085336, 1), (230687513, 1), (20906202, 2), (231539487, 2), (226755362, 1), (189268699, 1), (229770022, 2), (35979560, 1), (233898795, 1), (49479981, 1), (38732082, 1), (274072371, 1), (34799828, 1), (40173878, 2), (231473976, 1), (137429616, 1), (241238842, 1), (238224187, 1), (40632637, 1), (42533182, 14), (43254079, 4), (248513349, 1), (22479073, 3), (240976712, 2), (237437769, 1), (43581772, 2), (246678349, 1), (44892494, 1), (245171024, 1), (714540600, 2), (232129362, 1), (248775507, 1), (45220180, 2), (257295190, 1), (44695896, 2), (188416740, 1), (251593562, 1), (252707675, 2), (207356767, 1), (42008891, 4), (46989670, 2), (210174824, 1), (334037991, 1), (258540396, 2), (255853421, 1), (640812400, 1), (230622066, 1), (66126227, 1), (370869265, 1), (259130231, 2), (637666682, 5), (1188693892, 1), (61866390, 1), (646251913, 1), (153617047, 1), (10879085, 1), (59965837, 2), (737084909, 1), (62587281, 1), (62718355, 1), (290915221, 2), (366412694, 1), (288490391, 3), (35193050, 1), (366216090, 1), (62325147, 1), (69271965, 1), (68813214, 1), (235930437, 1), (69075362, 2), (68682150, 2), (301138856, 2), (71106987, 1), (151650966, 1), (300942255, 1), (312345520, 1), (42664264, 1), (70517173, 1), (71696822, 1), (312869815, 1), (318505912, 1), (305857465, 1), (67371423, 1), (307823550, 7), (304612287, 1), (72876481, 5), (5439571, 1), (128713291, 2), (470287521, 1), (308020170, 1), (313525195, 1), (301597602, 2), (319816655, 1), (322175954, 1), (317064147, 1), (319357912, 1), (320078809, 2), (321848282, 1), (735905243, 1), (325321693, 1), (323552223, 1), (320537568, 2), (548406523, 1), (104071652, 1), (99418597, 1), (90571239, 1), (249103185, 1), (44761426, 1), (38273334, 1), (91554290, 1), (97780211, 1), (247137108, 1), (96535033, 1), (93848063, 1)])

        page = self.w.db().find({'_id': id})
        self.assertEqual(dict(page['doc']), doc)

    def _digest(self):
        id = 12
        categories = [
                'Anarchism',
                'Political culture',
                'Political ideologies',
                'Social theories',
                'Anti-fascism',
                'Anti-capitalism'
                ]
        datetime = '2013-07-07T05:02:36Z'
        num_pagelinks = 735
        title = 'Anarchism'

        self.w.digest()

        if self.w.distrib:
            # There's probably a better way,
            # but if digestion is distrib,
            # wait until the task is complete.
            sleep(6)

        # Check that page data was added to db.
        # Check that non ns=0 page was ignored.
        self.assertEqual(self.w.db().count(), 1, 'Unexpected amount of documents were saved. Perhaps ns!=0 aren\'t being filtered?')

        # Check that page can be fetched by id.
        page = self.w.db().find({'_id': id})
        self.assertIsNotNone(page)

        # Check proper data.
        self.assertEqual(page['categories'], categories)
        self.assertGreaterEqual(len(page['pagelinks']), num_pagelinks)
        self.assertEqual(page['datetime'], datetime)
        self.assertEqual(page['title'], title)

    def _digest_updates(self):
        id = 12

        self.w.db().add({
            '_id': id,
            'categories': []
            })

        self.assertEqual(self.w.db().count(), 1)

        # Check that page can be fetched by id.
        page = self.w.db().find({'_id': id})
        self.assertIsNotNone(page)

        # Check that categories is empty.
        self.assertEqual(len(page['categories']), 0)

        self.w.digest()

        if self.w.distrib:
            # There's probably a better way,
            # but if digestion is distrib,
            # wait until the task is complete.
            sleep(6)

        self.assertEqual(self.w.db().count(), 1)

        page = self.w.db().find({'_id': id})
        self.assertIsNotNone(page)

        # Check that categories have been updated.
        self.assertGreater(len(page['categories']), 0)


if __name__ == '__main__':
	unittest.main()
