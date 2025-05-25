from os import environ

from photo_organizer.organizer import Organizer
from photo_organizer.server import Server


class App:
    def __init__(self) -> None:
        self._port = int(environ["PORT"])
        input_dir = environ["INPUT_DIR"]
        output_dir = environ["OUTPUT_DIR"]
        self._organizer = Organizer(input_dir, output_dir)

    def move_duplicates(self) -> None:
        self._organizer.move_duplicates()

    def move_non_photos(self) -> None:
        self._organizer.move_non_photos()

    def move_by_exif(self) -> None:
        self._organizer.move_by_exif()

    def run_date_server(self) -> None:
        Server.run(port=self._port, organizer=self._organizer)
