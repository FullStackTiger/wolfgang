#! /usr/bin/env bash

autopep8 --in-place --recursive wolfgang/
isort --recursive --skip wolfgang/client wolfgang/
flake8 wolfgang/