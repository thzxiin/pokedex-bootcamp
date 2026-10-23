"""Aplicação acadêmica local: HTTP + SQLite + PokéAPI, sem dependências externas."""
import json
import os
import re
import sqlite3
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, parse_qs
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DB_PATH = os.environ.get('DB_PATH', str(ROOT / 'data' / 'pokedex.sqlite3'))


def normalize_query(value):
    if not isinstance(value, str):
        raise ValueError('Informe o nome ou número do Pokémon.')
    value = value.strip().lower()
    if not re.fullmatch(r'[a-z0-9-]{1,50}', value):
        raise ValueError('Use um nome ou número válido, sem espaços ou símbolos.')
    return value


def fetch_pokemon(query):
    query = normalize_query(query)
    try:
        request = Request(
            f'https://pokeapi.co/api/v2/pokemon/{query}/',
            headers={'User-Agent': 'PokedexBootcamp/1.0', 'Accept': 'application/json'},
        )
        with urlopen(request, timeout=10) as response:
            data = json.load(response)
    except HTTPError as exc:
        if exc.code == 404:
            raise LookupError('Pokémon não encontrado.') from exc
        raise ConnectionError(f'A consulta à PokéAPI retornou HTTP {exc.code}. Tente novamente.') from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise ConnectionError('Não foi possível consultar a PokéAPI. Verifique a internet.') from exc
    return {'id': data['id'], 'name': data['name'],
            'image': data['sprites']['front_default'],
            'types': [item['type']['name'] for item in data['types']],
            'height': data['height'], 'weight': data['weight']}


def init_db(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute('CREATE TABLE IF NOT EXISTS favorites (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)')


def list_favorites(path):
    with closing(sqlite3.connect(path)) as conn:
        return [json.loads(row[0]) for row in conn.execute('SELECT payload FROM favorites ORDER BY id')]


def save_favorite(path, pokemon):
    with closing(sqlite3.connect(path)) as conn, conn:
        result = conn.execute('INSERT OR IGNORE INTO favorites VALUES (?, ?)',
                              (pokemon['id'], json.dumps(pokemon)))
        return result.rowcount == 1


def delete_favorite(path, pokemon_id):
    with closing(sqlite3.connect(path)) as conn, conn:
        return conn.execute('DELETE FROM favorites WHERE id = ?', (pokemon_id,)).rowcount == 1


def make_handler(db_path):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(status)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def run_action(self, action):
            try:
                action()
            except (ValueError, TypeError, json.JSONDecodeError):
                self.respond(400, {'error': 'Entrada inválida. Use um nome ou número de Pokémon.'})
            except LookupError as exc:
                self.respond(404, {'error': str(exc)})
            except ConnectionError as exc:
                self.respond(502, {'error': str(exc)})
            except sqlite3.Error:
                self.respond(500, {'error': 'Falha ao acessar o banco de dados.'})

        def do_GET(self):
            self.run_action(self.get)

        def get(self):
            url = urlsplit(self.path)
            if url.path == '/api/health':
                return self.respond(200, {'status': 'ok'})
            if url.path == '/api/favorites':
                return self.respond(200, list_favorites(db_path))
            if url.path == '/api/pokemon':
                query = parse_qs(url.query).get('q', [''])[0]
                return self.respond(200, fetch_pokemon(query))
            files = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'),
                     '/style.css': ('style.css', 'text/css')}
            if url.path not in files:
                return self.respond(404, {'error': 'Página não encontrada.'})
            name, mime = files[url.path]
            content = (ROOT / 'static' / name).read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', mime + '; charset=utf-8')
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
            self.run_action(self.post)

        def post(self):
            if self.path != '/api/favorites':
                return self.respond(404, {'error': 'Rota não encontrada.'})
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                return self.respond(415, {'error': 'Envie JSON.'})
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 4096:
                raise ValueError('Tamanho inválido.')
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError('Objeto obrigatório.')
            pokemon = fetch_pokemon(payload.get('query'))
            created = save_favorite(db_path, pokemon)
            self.respond(201 if created else 200, {'created': created, 'pokemon': pokemon})

        def do_DELETE(self):
            match = re.fullmatch(r'/api/favorites/(\d{1,8})', self.path)
            if not match:
                return self.respond(404, {'error': 'Rota não encontrada.'})
            def remove():
                deleted = delete_favorite(db_path, int(match[1]))
                self.respond(200 if deleted else 404, {'deleted': deleted})
            self.run_action(remove)
    return Handler


if __name__ == '__main__':
    init_db(DB_PATH)
    server = ThreadingHTTPServer((os.environ.get('HOST', '127.0.0.1'), int(os.environ.get('PORT', 8000))), make_handler(DB_PATH))
    print(f'Pokédex em http://localhost:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
