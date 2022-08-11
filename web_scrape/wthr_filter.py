#!/usr/bin/env python


# Import libraries
import pandas as pd
import numpy as np


# convert C to F rounded to 2 decimals
def cel_to_fahr(c):
    f = (c * (9/5)) + 32
    return round(f, 2)


# function to load weather data
def wthr_csv_to_df(wthr_csv):
    # import, clean, and sort data
    sta_pts = pd.read_csv("./temp_stations.csv")
    wthr_pts = pd.read_csv(wthr_csv)

    # subset only temperature data
    wthr_pts = wthr_pts[wthr_pts.wthr_dtype.isin(['TMAX', 'TMIN'])]

    # merge station and weather df's
    sta_wthr = pd.merge(sta_pts, wthr_pts, on='station_id')

    # create a column of datetime entries
    sta_wthr['DateTime'] = sta_wthr['date'].apply(lambda x: pd.to_datetime(str(x), format='%Y%m%d'))
    sta_wthr['month'] = sta_wthr['DateTime'].dt.month
    sta_wthr['year']  = sta_wthr['DateTime'].dt.year 

    # compute mean wthr value in each county for a given year month
    # and wthr_dtype  (TMIN, TMAX)
    wthr_grp_df = (sta_wthr.groupby(['county', 'year', 'month', 'wthr_dtype'])
                           .wthr_val.mean()
                           .reset_index())

    # convert wthr_val from tenths of Celsius to Fahrenheit
    wthr_grp_df['wthr_val'] = cel_to_fahr(wthr_grp_df['wthr_val'] / 10.)

    # convert to wide format using pivot
    wthr_grp_df = wthr_grp_df.pivot(index=['county', 'year', 'month'],
                                    columns='wthr_dtype', values='wthr_val')

    wthr_grp_df = wthr_grp_df.reset_index().rename_axis(None, axis=1)

    return wthr_grp_df


if __name__ == "__main__":
    data_name = "2016_2020_ca_wthr.csv"
    sta_wthr = wthr_csv_to_df("./" + data_name)
    # print("Filtering by month:", data_name)
    # print("Done!")
    # print(sta_wthr.head())

    # sanity check should have 58 counties
    # print("Number of unique counties present in data: ",
    #       len(sta_wthr.county.unique()))
    sta_wthr.to_csv('./2016_2020_ca_tmax_tmin_mnth.csv', index=False)
