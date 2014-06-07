#!/bin/bash

. ./local_config

set -e

TMPDIR=$(mktemp -d)

wget --quiet -O $TMPDIR/hare.zip $HARE_UPSTREAM_URL
unzip $TMPDIR/hare.zip -d $TMPDIR > /dev/null

iconv -f iso8859-1 -t utf8 < $TMPDIR/HARE-XML-Export-VM.xml > $TMPDIR/hare-utf8.xml

pypy conv-chars.py $TMPDIR/hare-utf8.xml > $TMPDIR/hare.xml

python import.py --output $TMPDIR/hare.json --mongo $TMPDIR/hare.xml

mongoimport --db hare --collection projects_import < $TMPDIR/hare.json
echo "db.projects_import.renameCollection('projects', true)" | mongo hare

