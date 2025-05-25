from functools import partial
from http.server import SimpleHTTPRequestHandler
from json import dumps
from logging import getLogger
from socket import socket
from socketserver import BaseServer, TCPServer
from urllib.parse import parse_qs, urlparse

from photo_organizer.organizer import Organizer

_logger = getLogger(__name__)


class Server:
    class Handler(SimpleHTTPRequestHandler):
        def __init__(
            self,
            request: socket | tuple[bytes, socket],
            client_address: str,
            server: BaseServer,
            organizer: Organizer,
        ):
            self._organizer = organizer
            super().__init__(request, client_address, server)

        def do_GET(self) -> None:
            url = urlparse(self.path)
            if url.path == "/" and "path=" not in url.query:
                # Add query with starting image
                next_path = self._organizer.get_next_path()
                new_url = f"/?path={next_path}"
                self.send_response(302)
                self.send_header("Location", new_url)
                self.end_headers()
            else:
                # Respond with index.html
                super().do_GET()

        def do_POST(self) -> None:
            # Move photo
            url = urlparse(self.path)
            parameters = parse_qs(url.query)
            [path] = parameters["path"]
            [year] = parameters["year"]
            self._organizer.move_file_to_dir(path, year)

            # Respond with next path
            self.send_response(200)
            self.end_headers()
            next_path = self._organizer.get_next_path()
            response = {"path": next_path}
            self.wfile.write(dumps(response).encode("utf-8"))

    class ReusableTcpServer(TCPServer):
        allow_reuse_address = True

    @staticmethod
    def run(port: int, organizer: Organizer) -> None:
        handler_initializer = partial(Server.Handler, organizer=organizer)
        with Server.ReusableTcpServer(("", port), handler_initializer) as server:
            _logger.info(f"Serving at http://localhost:{port}")
            server.serve_forever()
