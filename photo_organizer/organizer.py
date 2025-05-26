from hashlib import sha256
from logging import getLogger
from mimetypes import guess_type
from pathlib import Path
from random import choices
from re import sub
from shutil import move
from string import ascii_letters, digits
from typing import ClassVar, cast

from PIL import Image
from PIL.ExifTags import TAGS
from PIL.Image import Exif

_logger = getLogger(__name__)


class Organizer:
    _DATE_TAGS: ClassVar[list[str]] = [
        "DateTimeOriginal",  # Most accurate: when the photo was actually taken
        "SubsecDateTimeOriginal",  # Same as above, but with sub-second precision (if available)
        "DateTimeDigitized",  # When the image was digitized (e.g. scanned from film)
        "DateTime",  # When the file was last modified (not necessarily creation)
        "CreateDate",  # Used in XMP metadata; sometimes present in modern files
        "ModifyDate",  # Also from XMP/IPTC, last modified time
        "GPSDateStamp",  # Date from GPS metadata (in UTC), often paired with GPSTimeStamp
    ]

    def __init__(self, input_dir: str, output_dir: str):
        self._input_dir = input_dir
        self._output_dir = output_dir

    def get_next_path(self) -> str | None:
        root = Path(self._input_dir)
        paths = sorted([p for p in root.rglob("*") if p.is_file()])
        return f"{paths[0]}" if len(paths) else None

    def move_file_to_dir(self, path: str, dir: str) -> None:
        input_path = Path(path)
        output_path = Path(self._output_dir, dir, Organizer.get_simple_filename(path))

        # Create destination directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)

        _logger.info(f"Moving {input_path} -> {output_path}")

        # Move the file
        move(f"{input_path}", f"{output_path}")

    def move_by_exif(self) -> None:
        root = Path(self._input_dir)
        paths = sorted([p for p in root.rglob("*") if p.is_file()])
        for path in paths:
            year = Organizer.extract_year(path)
            if year:
                _logger.info(f"Found year: {year}")
                self.move_file_to_dir(path=f"{path}", dir=year)

    def move_duplicates(self) -> None:
        root = Path(self._input_dir)
        paths = sorted([p for p in root.rglob("*") if p.is_file()])
        _logger.info("Finding duplicates...")
        duplicates = Organizer.find_duplicates(paths)
        for group in duplicates:
            _logger.info("Found dup")
            for path in group[1:]:
                self.move_file_to_dir(path=path, dir="Duplicate")

    def convert_images(self, mime_type: str) -> None:
        root = Path(self._input_dir)
        paths = sorted([p for p in root.rglob("*") if p.is_file()])
        selected_paths = [p for p in paths if Organizer.is_mime_type(mime_type, f"{p}")]
        for path in selected_paths:
            _logger.info(f"Found {mime_type} to convert")
            Organizer.convert_to_png(f"{path}")

        _logger.info(f"Converted all {mime_type}")
        for path in selected_paths:
            path.unlink()

    @staticmethod
    def is_image(path: str) -> bool:
        mime_type, _ = guess_type(path)
        if mime_type:
            if mime_type.startswith("image/"):
                try:
                    with Image.open(path) as _:
                        return True
                except Exception:
                    pass
        return False

    @staticmethod
    def is_mime_type(type: str, path: str) -> bool:
        mime_type, _ = guess_type(path)
        return mime_type == type

    def move_non_photos(self) -> None:
        root = Path(self._input_dir)
        paths = sorted([f"{p}" for p in root.rglob("*") if p.is_file()])
        for path in paths:
            if not Organizer.is_image(path):
                self.move_file_to_dir(path=path, dir="Non-Image")

    @staticmethod
    def get_simple_filename(subject: str) -> str:
        santized = sub(r"[^a-zA-Z0-9\.]+", "-", subject)
        last_61 = santized[-61:]
        # Add uniqness to avoid overwriting
        uniqueness = Organizer.generate_random_characters(3)
        return f"{uniqueness}{last_61}"

    @staticmethod
    def generate_random_characters(length: int) -> str:
        chars = ascii_letters + digits  # a-zA-Z0-9
        return "".join(choices(chars, k=length)).lower()

    @staticmethod
    def calculate_checksum(path: Path) -> str:
        hasher = sha256()
        with path.open("rb") as f:
            content = f.read()
        hasher.update(content)
        return hasher.hexdigest()

    @staticmethod
    def find_duplicates(paths: list[Path]) -> list[list[str]]:
        checksums: dict[str, list[str]] = {}

        for path in paths:
            sha = Organizer.calculate_checksum(path)
            checksums.setdefault(sha, []).append(f"{path}")

        duplicates = [group for group in checksums.values() if len(group) > 1]
        return duplicates

    @staticmethod
    def extract_year(path: Path) -> str | None:
        with Image.open(path) as img:
            exif = img.getexif()
            if not exif:
                return None
        date_raw = Organizer.get_first_exif_date(exif)
        if not date_raw:
            return None
        year, *_ = date_raw.split(":")
        if year == "0000":
            _logger.info(f"Bad Year {date_raw}")
            return None
        return year

    @staticmethod
    def get_first_exif_date(exif: Exif) -> str | None:
        tags = {TAGS.get(tag_id, tag_id): value for tag_id, value in exif.items()}
        for tag in Organizer._DATE_TAGS:
            if tag in tags:
                return cast(str, tags[tag])
        return None

    @staticmethod
    def convert_to_png(path: str) -> None:
        try:
            with Image.open(path) as image:
                image.save(f"{path}.png", format="PNG")
        except Exception:
            _logger.exception(path)
