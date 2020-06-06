#! /usr/bin/env bash

cd /app/wolfgang/client/app
npm install
npm rebuild node-sass --force
npm run build # necessary to run flask

cd /app/

until mysql -h wolfdb -uwolfgang_dev -pwolfgang_dev_password -e exit; do
  echo "Mysql is unavailable - sleeping"
  sleep 1
done

mysql -h wolfdb -P 3306 -uroot -proot_dev_password --execute="DROP DATABASE IF EXISTS wolfgang; CREATE DATABASE wolfgang;"

rm -rf migrations
flask db init
# [[ -d "migrations" ]] || flask db init # Only run if migrations dir doesn't exist
flask db migrate
flask db upgrade

echo "Populating geo tables:"
wget --no-check-certificate http://download.geonames.org/export/dump/countryInfo.txt
sed -i '/^#/d' countryInfo.txt
mysql -h wolfdb -P 3306 --local-infile -uroot -proot_dev_password wolfgang --execute="SET FOREIGN_KEY_CHECKS = 0; LOAD DATA LOCAL INFILE 'countryInfo.txt' INTO TABLE country FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' (iso, iso3, iso_numeric, fips, name, capital, area, population, continent, tld, currency_code, currency_name, phone, postal_code_format, postal_code_regex, languages, geoname_id, neighbours, equivalent_fips_code); SET FOREIGN_KEY_CHECKS = 1;"
rm countryInfo.txt

gunzip -f -k scripts/geoname_filtered.txt
 mysql -h wolfdb -P 3306 --local-infile -uroot -proot_dev_password wolfgang --execute="SET FOREIGN_KEY_CHECKS = 0; LOAD DATA LOCAL INFILE 'scripts/geoname_filtered.txt' INTO TABLE geoname FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' (geoname_id, name, ascii_name, alternate_names, latitude, longitude, feature_class, feature_code, country_code, cc2, admin1_code, admin2_code, admin3_code, admin4_code, population, elevation, dem, timezone, modification_date) SET elevation = nullif(@elevation, ''), dem = nullif(@dem, ''); SET FOREIGN_KEY_CHECKS = 1;"
rm scripts/geoname_filtered.txt

flask insert_dev_data # defined in commands.py

flask run --host=0.0.0.0 --port=$FLASK_PORT &

cd /app/wolfgang/client/app
yarn start
