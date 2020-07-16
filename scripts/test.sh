#!/usr/bin/env bash

set -e
set -x

bash ./scripts/lint.sh
pytest --cov=split_schedule --cov-report=term-missing
