SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c

ALL_WTHR_CSV = $(shell echo srcp_data/wthr_{2016..2020}.csv)

.PHONY: all clean distclean


all: 2016_2020_ca_tmax_tmin_mnth.csv

scrp_data:
	mkdir $@
	parallel "curl -sOL  'https://www1.ncdc.noaa.gov/pub/data/ghcn/daily/by_year/{}.csv.gz';
	  gunzip -c {}.csv.gz > $@/wthr_{}.csv" ::: {2016..2020}

$(ALL_WTHR_CSV): scrp_data

tmp_data: $(ALL_WTHR_CSV)
	mkdir $@

2016_2020_ca_wthr.csv: tmp_data temp_station_ids
	parallel "<scrp_data/wthr_{1}.csv grep {2} | 
	    cut -d, -f 1,2,3,4 > tmp_data/tmp_wthr_{1}_{2}.csv" ::: {2016..2020} :::: temp_station_ids
	echo 'station_id,date,wthr_dtype,wthr_val' > $@
	cat tmp_data/* >> $@

wthr_filter.py: 2016_2020_ca_wthr.csv temp_stations.csv

2016_2020_ca_tmax_tmin_mnth.csv: 2016_2020_ca_wthr.csv wthr_filter.py
	./wthr_filter.py

clean:
	rm -rf scrp_data tmp_data {2016..2020}.csv.gz

distclean: 
	rm -rf scrp_data tmp_data {2016..2020}.csv.gz
	rm -rf 2016_2020_ca_wthr.csv 2016_2020_ca_tmax_tmin_mnth.csv
