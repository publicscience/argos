import unittest
from unittest.mock import MagicMock

from tests import RequiresMocks

from argos.core import knowledge

class KnowledgeTest(RequiresMocks):
    def setUp(self):
        self.mock_resp = MagicMock()
        self.mock_resp.status = 200
        self.create_patch('urllib.request.urlopen', return_value=self.mock_resp)

    def test_sanitize_names(self):
        name = 'Trailer Song" Live'
        s_name = knowledge._sanitize(name)
        self.assertEqual(s_name, 'Trailer Song\\" Live')

    def test_uri_for_name(self):
        self.mock_resp.read.return_value = b'{\n  "head": {\n    "vars": [ "uri" ]\n  } ,\n  "results": {\n    "bindings": [\n      {\n        "uri": { "type": "uri" , "value": "http://dbpedia.org/resource/United_States_Secretary_of_State" }\n      }\n    ]\n  }\n}\n'
        uri = knowledge.uri_for_name('United States Secretary of State')
        self.assertEqual(uri, 'http://dbpedia.org/resource/United_States_Secretary_of_State')

    def test_types_for_uri(self):
        self.mock_resp.read.return_value = b'''
            {
              "head": {
                "vars": [ "type" ]
              } ,
              "results": {
                "bindings": [
                  {
                    "type": { "type": "uri" , "value": "http://schema.org/Organization" }
                  } ,
                  {
                    "type": { "type": "uri" , "value": "http://dbpedia.org/ontology/Company" }
                  }
                ]
              }
            }
        '''
        types = knowledge.types_for_uri('http://dbpedia.org/resource/Google')
        self.assertEqual(types, ['http://schema.org/Organization', 'http://dbpedia.org/ontology/Company'])

    def test_image_for_uri(self):
        self.mock_resp.read.return_value = b'{\n  "head": {\n    "vars": [ "image_url" ]\n  } ,\n  "results": {\n    "bindings": [\n      {\n        "image_url": { "type": "uri" , "value": "http://upload.wikimedia.org/wikipedia/commons/7/7e/StarTrek_Logo_2007.JPG" }\n      }\n    ]\n  }\n}\n'
        image_url = knowledge.image_for_uri('http://dbpedia.org/resource/Star_Trek')
        self.assertEqual(image_url, 'http://upload.wikimedia.org/wikipedia/commons/7/7e/StarTrek_Logo_2007.JPG')

    def test_coordinates_for_uri(self):
        self.mock_resp.read.return_value = b'{\n  "head": {\n    "vars": [ "lat" , "long" ]\n  } ,\n  "results": {\n    "bindings": [\n      {\n        "lat": { "datatype": "http://www.w3.org/2001/XMLSchema#float" , "type": "typed-literal" , "value": "39.90638888888889" } ,\n        "long": { "datatype": "http://www.w3.org/2001/XMLSchema#float" , "type": "typed-literal" , "value": "116.37972222222223" }\n      }\n    ]\n  }\n}\n'
        coordinates = knowledge.coordinates_for_uri('http://dbpedia.org/resource/Beijing')
        self.assertEqual(coordinates, {'lat': '39.90638888888889', 'long': '116.37972222222223'})

    def test_summary_for_uri(self):
        self.mock_resp.read.return_value = b'{\n  "head": {\n    "vars": [ "summary" ]\n  } ,\n  "results": {\n    "bindings": [\n      {\n        "summary": { "type": "literal" , "xml:lang": "en" , "value": "this is a summary" }\n      }\n    ]\n  }\n}\n'
        summary = knowledge.summary_for_uri('http://dbpedia.org/resource/Beijing')
        self.assertEqual(summary, "this is a summary")

    def test_aliases_for_uri(self):
        self.mock_resp.read.return_value = b'{\n  "head": {\n    "vars": [ "alias_uri" ]\n  } ,\n  "results": {\n    "bindings": [\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/StarTrek" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_trek" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/The_Enterprise_Crew" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Startrek" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star-Trek" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_Trek_The_Beginning" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_tek" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_Trek_video" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_Treck" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_Trek-TNG" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_Trek_universe" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/The_Star_Trek_Franchise" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/StarTrek.com" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Startrek.com" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_Trek:_Continuum" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_Trek_Continuum" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_trec" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Murasaki_312" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Startreck" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_Trek_franchise" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Sonic_shower" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/History_of_the_Star_Trek_franchise" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_Trek_(franchise)" }\n      } ,\n      {\n        "alias_uri": { "type": "uri" , "value": "http://dbpedia.org/resource/Star_trek.com" }\n      }\n    ]\n  }\n}\n'
        aliases = knowledge.aliases_for_uri('http://dbpedia.org/resource/Star_Trek')
        self.assertEqual(aliases, ['http://dbpedia.org/resource/StarTrek',
                                 'http://dbpedia.org/resource/Star_trek',
                                 'http://dbpedia.org/resource/The_Enterprise_Crew',
                                 'http://dbpedia.org/resource/Startrek',
                                 'http://dbpedia.org/resource/Star-Trek',
                                 'http://dbpedia.org/resource/Star_Trek_The_Beginning',
                                 'http://dbpedia.org/resource/Star_tek',
                                 'http://dbpedia.org/resource/Star_Trek_video',
                                 'http://dbpedia.org/resource/Star_Treck',
                                 'http://dbpedia.org/resource/Star_Trek-TNG',
                                 'http://dbpedia.org/resource/Star_Trek_universe',
                                 'http://dbpedia.org/resource/The_Star_Trek_Franchise',
                                 'http://dbpedia.org/resource/StarTrek.com',
                                 'http://dbpedia.org/resource/Startrek.com',
                                 'http://dbpedia.org/resource/Star_Trek:_Continuum',
                                 'http://dbpedia.org/resource/Star_Trek_Continuum',
                                 'http://dbpedia.org/resource/Star_trec',
                                 'http://dbpedia.org/resource/Murasaki_312',
                                 'http://dbpedia.org/resource/Startreck',
                                 'http://dbpedia.org/resource/Star_Trek_franchise',
                                 'http://dbpedia.org/resource/Sonic_shower',
                                 'http://dbpedia.org/resource/History_of_the_Star_Trek_franchise',
                                 'http://dbpedia.org/resource/Star_Trek_(franchise)',
                                 'http://dbpedia.org/resource/Star_trek.com'])


    def test_name_for_uri(self):
        self.mock_resp.read.return_value = b'{\n  "head": {\n    "vars": [ "name" ]\n  } ,\n  "results": {\n    "bindings": [\n      {\n        "name": { "type": "literal" , "xml:lang": "en" , "value": "United States Secretary of State" }\n      }\n    ]\n  }\n}\n'

        name = knowledge.name_for_uri('http://dbpedia.org/resource/United_States_Secretary_of_State')
        self.assertEqual(name, 'United States Secretary of State')

    def test_pagelinks_for_uri(self):
        self.mock_resp.read.return_value = b'''
            {
                "head": {
                    "vars": [ "from" ]
                } ,
                "results": {
                    "bindings": [
                        {
                            "from": { "type": "uri" , "value": "http://dbpedia.org/resource/Taiping_Rebellion" }
                        } ,
                        {
                            "from": { "type": "uri" , "value": "http://dbpedia.org/resource/Taiping_Heavenly_Kingdom" }
                        }
                    ]
                }
            }
        '''
        pagelinks = knowledge.pagelinks_for_uri('http://dbpedia.org/resource/Zeng_Guofan')
        self.assertEqual(len(pagelinks), 2)

    def test_commonness_for_uri(self):
        self.mock_resp.read.return_value = b'''
            {
                "head": {
                    "vars": [ "from" ]
                } ,
                "results": {
                    "bindings": [
                        {
                            "from": { "type": "uri" , "value": "http://dbpedia.org/resource/Taiping_Rebellion" }
                        } ,
                        {
                            "from": { "type": "uri" , "value": "http://dbpedia.org/resource/Taiping_Heavenly_Kingdom" }
                        }
                    ]
                }
            }
        '''
        commonness = knowledge.commonness_for_uri('http://dbpedia.org/resource/Zeng_Guofan')
        self.assertEqual(commonness, 2)


class KnowledgeProfilesTest(RequiresMocks):
    def test_company_profile(self):
        self.mock_types = self.create_patch('argos.core.knowledge.types_for_uri')
        self.mock_types.return_value = ['http://dbpedia.org/ontology/Company']

        profile = knowledge.profiles.get_profile('http://dbpedia.org/resource/Google')

        self.assertEqual(profile['type'], 'company')

    def test_place_profile(self):
        self.mock_types = self.create_patch('argos.core.knowledge.types_for_uri')
        self.mock_types.return_value = ['http://dbpedia.org/ontology/Place']

        profile = knowledge.profiles.get_profile('http://dbpedia.org/resource/Syria')

        self.assertEqual(profile['type'], 'place')


class KnowledgeSpecialTest(RequiresMocks):
    """
    SPARQL can be really sensitive about certain
    characters. These tests are to check that
    they are properly handled.
    """

    def test_single_quotes_uri(self):
        test_uris = [
            "http://dbpedia.org/resource/O'Reilly_Media",
            "http://dbpedia.org/resource/O'Reilly'_Media",
        ]
        for uri in test_uris:
            knowledge.name_for_uri(uri)
            knowledge.summary_for_uri(uri)
            knowledge.coordinates_for_uri(uri)
            knowledge.image_for_uri(uri)
            knowledge.aliases_for_uri(uri)

    def test_double_quotes_uri(self):
        test_uris = [
            'http://dbpedia.org/resource/O"Reilly_Media',
            'http://dbpedia.org/resource/O"Reilly"_Media'
        ]
        for uri in test_uris:
            knowledge.name_for_uri(uri)
            knowledge.summary_for_uri(uri)
            knowledge.coordinates_for_uri(uri)
            knowledge.image_for_uri(uri)
            knowledge.aliases_for_uri(uri)

    def test_ampersands_name(self):
        test_names = [
            'Foo & Bar'
        ]
        for name in test_names:
            knowledge.uri_for_name(name)
            knowledge.summary_for_name(name)
            knowledge.coordinates_for_name(name)
            knowledge.image_for_name(name)
            knowledge.aliases_for_name(name)

if __name__ == '__main__':
	unittest.main()
