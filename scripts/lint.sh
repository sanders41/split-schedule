#!/usr/bin/env bash

set -e
set -x

mypy split_schedule
black split_schedule tests --check