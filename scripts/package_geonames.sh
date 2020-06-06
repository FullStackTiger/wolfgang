#!/bin/bash

DB_USER=irlster
DB_PWD=yQwcYQEt6DmfmDYN
DB=irlster

### This script generates pre-packaged files

echo "Populating GeoName... (this might take a while)"
wget --no-check-certificate http://download.geonames.org/export/dump/allCountries.zip
unzip allCountries.zip
rm allCountries.zip
### Only keeping feature class A & other port-related stuff (do we need P?)

awk -F\t '($7=="A" && $8 != "") || $8=="PRT" || $8 == "NVB" || $8 == "JTY" || $8 == "LDNG" || $8 =="DCKB" || $8 == "HBR" || $8 == "HBRX" || $8 == "RDST" || $8 == "MAR"' allCountries.txt > geoname_filtered_1.txt

#### NEED TO REMOVE 4+ byte chars: [\x{10000}-\x{10FFFF}]+

awk -F $'\t' '$7=="A"' allCountries.txt > geoname_filtered_2.txt

rm allCountries.txt

mysql --local-infile -u$DB_USER -p$DB_PWD $DB --execute="SET FOREIGN_KEY_CHECKS = 0; LOAD DATA LOCAL INFILE 'geoname_filtered.txt' INTO TABLE geonames FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' (geoname_id, name, asciiName, @alternateNames_skipped, latitude, longitude, featureClass, featureCode, countryCode, cc2, admin1Code, admin2Code, admin3Code, admin4Code, population, @elevation, dem, timezone, modificationDate) SET elevation = nullif(@elevation, ''); SET FOREIGN_KEY_CHECKS = 1;"

rm geoname_filtered.txt

wget --no-check-certificate http://download.geonames.org/export/dump/countryInfo.txt
sed -i '' '/^#/d' countryInfo.txt

# echo "Generating Sphinx indexes (this will also take a while)"
# ### TODO: make sure Sphinx and Sphinx PHP are installed
# # cd ../app/config
# mkdir ./search-data
# PATH_TO_INDEX="`pwd`/search-data"
# PATH_TO_MYSQL_SOCK=`mysqladmin variables | grep '\| socket' | awk -F" " '{print $4}'`
# cat sphinx.conf.template | sed -e "s,\${PATH_TO_INDEXES},$PATH_TO_INDEX," -e "s,\${PATH_TO_MYSQL_SOCK},$PATH_TO_MYSQL_SOCK," -e "s,\${DB_PWD},$DB_PWD,"  > sphinx.conf
# ### TODO: package default indexes instead of generating from
# #  indexer -c sphinx.conf --rotate --all
# indexer -c sphinx.conf --all
# echo "Done."
#
# echo "Restarting sphinx:"
# killall searchd
# searchd -c sphinx.conf
