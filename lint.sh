#/bin/sh

set -euxo pipefail

ruff format --check
ruff check
mypy .