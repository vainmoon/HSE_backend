#!/bin/sh
pgmigrate -c db/migrations.yml -t latest migrate
exec "$@"