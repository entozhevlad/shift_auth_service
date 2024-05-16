#!/bin/sh
apt list --installed
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true
