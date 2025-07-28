import time
from functools import partial
import os
import threading
import socket
import webbrowser
from http import server
from socketserver import ThreadingMixIn
from urllib.parse import quote_plus

class QuietHTTPRequestHandler(server.SimpleHTTPRequestHandler):
    """Handler qui supprime les logs de chaque requête."""
    def log_message(self, format, *args):
        pass

class ThreadingHTTPServer(ThreadingMixIn, server.HTTPServer):
    """Serveur HTTP multi-threads; threads en daemon pour s'arrêter facilement."""
    daemon_threads = True
    allow_reuse_address = True

class DocServer:
    def __init__(self, nm, doc_path="docs", port_start=8000, port_end=8100, cooldown=5):
        self.nm = nm
        self.doc_path = os.path.abspath(doc_path)
        self.port_start = port_start
        self.port_end = port_end
        self.httpd = None
        self.thread = None
        self.port = None

        # Dictionnaire query -> timestamp de la dernière ouverture
        self._last_help_call = {}
        # délai minimal (en secondes) entre deux appels sur la même query
        self._cooldown = cooldown

    def _find_free_port_and_start(self):
        if self.httpd:
            return

        for port in range(self.port_start, self.port_end + 1):
            try:
                handler_cls = partial(QuietHTTPRequestHandler, directory=self.doc_path)
                self.httpd = ThreadingHTTPServer(("", port), handler_cls)
                self.port = port
                break
            except OSError as e:
                if e.errno == socket.errno.EADDRINUSE:
                    continue
                raise
        else:
            self.nm.notify(
                'error',
                'Impossible de lancer la documentation',
                f"Aucun port libre entre {self.port_start} et {self.port_end}",
                duration=4
            )
            return

        self.thread = threading.Thread(
            target=self.httpd.serve_forever,
            name="DocServerThread",
            daemon=True
        )
        self.thread.start()

    def open_docs(self):
        """
        Ouvre la page index.html dans le navigateur.
        Démarre le serveur si nécessaire.
        """
        self._find_free_port_and_start()
        url = f"http://localhost:{self.port}/index.html"
        webbrowser.open(url)

    def help(self, query: str):
        """
        Ouvre la page références.html?search=<query> dans le navigateur.
        Applique un cooldown pour empêcher les répétitions trop rapides.
        """
        now = time.time()
        last = self._last_help_call.get(query, 0)

        if now - last < self._cooldown:
            # Si on rappelle trop vite la même query, on bloque
            self.nm.notify(
                'error',
                "Trop de requêtes identiques",
                f"Veuillez patienter {int(self._cooldown - (now - last))} s avant de relancer \" {query} \"",
                duration=3
            )
            return

        # Sinon, on mémorise le timestamp et on ouvre
        self._last_help_call[query] = now
        self._find_free_port_and_start()
        q = quote_plus(query)
        url = f"http://localhost:{self.port}/pages/references.html?search={q}"
        webbrowser.open(url)

    def stop(self):
        """
        Arrête proprement le serveur.
        """
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.thread.join(timeout=1)
            self.httpd = None
            self.thread = None
            self.port = None

