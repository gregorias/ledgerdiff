# 🧰 Developer Documentation

This document is meant for developers and provides instruction on how to work
with the repository.

## Dev Environment Setup

This project requires [Lefthook](https://github.com/evilmartians/lefthook) and
[Commitlint](https://github.com/conventional-changelog/commitlint).

Install lefthook:

```bash
lefthook install
```

Also install [direnv](https://direnv.net/) to benefit from some dev tools.

## Updating dependencies

To update locked dependencies, run

```shell
uv sync
```

From time to time, check if the major versions of dependencies in
`pyproject.toml` need updating.

## Updating Python version

To update the Python version used in the virtual environment, run:

```shell
uv venv --clear --python 3.13
uv sync
```
