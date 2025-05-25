from logging import INFO, basicConfig

from photo_organizer.app import App


def main() -> None:
    basicConfig(level=INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    app = App()
    # app.move_duplicates()
    # app.move_non_photos()
    # app.move_by_exif()
    # TODO convert TIF
    app.run_date_server()


main()
