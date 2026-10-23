import json
import tempfile
import threading
import unittest
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from unittest.mock import patch, MagicMock
from urllib.error import HTTPError, URLError
from app import (normalize_query, init_db, save_favorite, list_favorites,
                 delete_favorite, fetch_pokemon, make_handler)

PIKACHU = {'id': 25, 'name': 'pikachu', 'image': None, 'types': ['electric'], 'height': 4, 'weight': 60}


class ValidationTests(unittest.TestCase):
    def test_normalizes_name(self):
        self.assertEqual(normalize_query(' Pikachu '), 'pikachu')

    def test_rejects_invalid_queries(self):
        for value in ['', '   ', '../etc', '<script>', None, 25, 'a' * 51]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_query(value)

    def test_accepts_id_and_hyphen(self):
        self.assertEqual(normalize_query('25'), '25')
        self.assertEqual(normalize_query('mr-mime'), 'mr-mime')


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = self.temp.name + '/db.sqlite3'
        init_db(self.path)

    def test_create_list_delete(self):
        self.assertTrue(save_favorite(self.path, PIKACHU))
        self.assertEqual(list_favorites(self.path), [PIKACHU])
        self.assertTrue(delete_favorite(self.path, 25))
        self.assertEqual(list_favorites(self.path), [])

    def test_no_duplicates(self):
        save_favorite(self.path, PIKACHU)
        self.assertFalse(save_favorite(self.path, PIKACHU))
        self.assertEqual(len(list_favorites(self.path)), 1)

    def test_persistence_after_reinitialize(self):
        save_favorite(self.path, PIKACHU)
        init_db(self.path)
        self.assertEqual(list_favorites(self.path), [PIKACHU])

    def test_delete_missing(self):
        self.assertFalse(delete_favorite(self.path, 999))


class ApiTests(unittest.TestCase):
    @patch('app.urlopen')
    def test_maps_external_response(self, mock):
        data = {'id':25, 'name':'pikachu', 'sprites':{'front_default':None},
                'types':[{'type':{'name':'electric'}}], 'height':4, 'weight':60}
        mock.return_value.__enter__.return_value.read.return_value = json.dumps(data).encode()
        self.assertEqual(fetch_pokemon('Pikachu'), PIKACHU)
        mock.assert_called_once()
        request = mock.call_args.args[0]
        self.assertEqual(request.full_url, 'https://pokeapi.co/api/v2/pokemon/pikachu/')
        self.assertEqual(request.get_header('Accept'), 'application/json')
        self.assertEqual(request.get_header('User-agent'), 'PokedexBootcamp/1.0')
        self.assertEqual(mock.call_args.kwargs['timeout'], 10)

    @patch('app.urlopen', side_effect=HTTPError('url', 404, 'missing', {}, None))
    def test_external_not_found(self, mock):
        with self.assertRaises(LookupError):
            fetch_pokemon('not-a-pokemon')

    @patch('app.urlopen', side_effect=URLError('offline'))
    def test_external_unavailable(self, mock):
        with self.assertRaises(ConnectionError):
            fetch_pokemon('pikachu')


class HttpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.path = cls.temp.name + '/db.sqlite3'
        init_db(cls.path)
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), make_handler(cls.path))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        cls.temp.cleanup()

    def request(self, method, path, body=None, headers=None):
        conn = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        try:
            conn.request(method, path, body, headers or {})
            response = conn.getresponse()
            return response.status, response.read()
        finally:
            conn.close()

    def test_page_and_health(self):
        status, body = self.request('GET', '/')
        self.assertEqual(status, 200)
        self.assertIn(b'POK', body)
        self.assertEqual(self.request('GET', '/api/health')[0], 200)

    @patch('app.fetch_pokemon', return_value=PIKACHU)
    def test_full_http_crud(self, mock):
        status, _ = self.request('POST', '/api/favorites', '{"query":"25"}', {'Content-Type':'application/json'})
        self.assertEqual(status, 201)
        status, body = self.request('GET', '/api/favorites')
        self.assertEqual(json.loads(body), [PIKACHU])
        self.assertEqual(self.request('DELETE', '/api/favorites/25')[0], 200)
        self.assertEqual(self.request('DELETE', '/api/favorites/25')[0], 404)

    def test_invalid_input_and_routes(self):
        self.assertEqual(self.request('GET', '/api/pokemon?q=..')[0], 400)
        self.assertEqual(self.request('GET', '/../app.py')[0], 404)
        self.assertEqual(self.request('POST', '/api/favorites', '{}')[0], 415)
        self.assertEqual(self.request('POST', '/api/favorites', '[1]', {'Content-Type':'application/json'})[0], 400)
