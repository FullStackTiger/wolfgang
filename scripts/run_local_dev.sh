#! /usr/bin/env bash

eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
export FLASK_APP=autoapp.py
export FLASK_DEBUG=1
export WOLFGANG_SECRET='dev-secret'
export PYTHONDONTWRITEBYTECODE=1 # optional: disable generation of binary files and cache
export WOLFGANG_REST_SERVER=localhost:5000
export WOLFGANG_CORS=1 # allows running debug frontend on separate server

cd ./wolfgang/client/app
# Comment next line once everyone has 'fresh' node_modules
rm -rf node_modules
npm install
# Build the app for production (index.html and assets -> http://localhost:5000)
npm run build
# Start the app in dev mode (webpack-dev-server -> http://localhost:8080)
# npm start
cd -

## Activate python env and install flask requirements:
pyenv activate wolfgang-env
pip install -r requirements/dev.txt

## Take care of Flask DB migrations:
rm -rf migrations #TODO: freeze first version of DB and add migrations to repo (and remove command)
rm local_dev.db #remove with line above
flask db init
flask db migrate
flask db upgrade
echo "Populating geo tables:"
wget --no-check-certificate http://download.geonames.org/export/dump/countryInfo.txt
sed -i.bak '/^#/d' countryInfo.txt
rm countryInfo.txt.bak
echo -e ".mode tabs\n.import countryInfo.txt country" | sqlite3 local_dev.db 
rm countryInfo.txt
gunzip -k -f scripts/geoname_filtered.txt.gz 
echo -e ".mode tabs\n.import scripts/geoname_filtered.txt geoname" | sqlite3 local_dev.db 
rm scripts/geoname_filtered.txt
flask insert_dev_data # defined in commands.py

flask run
