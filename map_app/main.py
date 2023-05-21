import pandas as pd
import numpy as np
import math
import os

import geopandas
import json

from calendar import month_abbr

from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter
from bokeh.palettes import brewer

from bokeh.io.doc import curdoc
from bokeh.models import Slider, HoverTool, Select
from bokeh.layouts import column, Column
from bokeh.themes import built_in_themes, Theme

data_stem_pth = os.path.join(os.getcwd(), 'map_app', 'data')

theme_pth = os.path.join(os.getcwd(), 'map_app', 'templates', 'theme.yml')

# load weather data
sta_wthr_pth = os.path.join(data_stem_pth, '2016_2020_ca_tmax_tmin_mnth.csv')
sta_wthr = pd.read_csv(sta_wthr_pth)

# sanity check should have 58 counties
# print(len(sta_wthr.county.unique()))

# load geojson files
geojson_pth = os.path.join(data_stem_pth, 'CA_Counties_TIGER2016.geojson')
ca = geopandas.read_file(geojson_pth)

# define cooredinate reference system for data projection
# ESPG code 4326 is equiv to WGS84 lat-long projection
ca.crs = 'epsg:4326' 

ca = ca.rename(columns={'NAME':'county'}) 

# check to see if names are identical: True
# print("Are the county names of ca geopandas identical to weather station data: ",
#       set(ca.county) == set(sta_wthr.county.unique()))


# function to return json_data for a user selected month and year
def json_wthr_data(selec_yr, selec_mnth):
    yr = selec_yr
    mnth = selec_mnth

    # rip selected month and year from the weather station data
    selec_df = sta_wthr[(sta_wthr['month'] == mnth) & (sta_wthr['year'] == yr)]

    # combine ca (GeoDataframe) with filtered weather station data
    df_mrgd = pd.merge(ca, selec_df, on ='county', how='left')

    # NA values to be filled
    vals = {'year': yr, 'month': mnth}
    df_mrgd = df_mrgd.fillna(value=vals)

    # convert to df to json
    json_mrgd = json.loads(df_mrgd.to_json())

    # convert to json string-like object
    json_data = json.dumps(json_mrgd)

    return json_data


################################################################################
################# Interactive Map ##############################################
################################################################################

# df to help with selecting either max or min temp data
# during plot creation and update callbacks
plt_scheme_data = [('TMAX', 0, 130, '0,0', 'Average Maximum Temperature'),
               ('TMIN', 0, 130, '0,0', 'Average Minimum Temperature')]

plt_scheme_df = pd.DataFrame(plt_scheme_data, columns=['field', 'min_range', 'max_range',
                                               'format', 'text'])

# name_of_mnth: number_of_mnth
mnth_dict = {b:a for a, b in enumerate(month_abbr[1::], start=1)}


# map callback function: update_plot
def update_plot(attr, old, new):
    # the input yr is the year selected from the slider_yr
    yr = slider_yr.value
    mnth_txt = select_mnth.value
    mnth = mnth_dict[mnth_txt]

    # generate geojsondata for a given year and month
    new_data = json_wthr_data(yr, mnth)

    # the input tmp_dtype is either TMAX or TMIN input from select_temp box
    tmp_dtype = select_temp.value
    input_field = plt_scheme_df.loc[plt_scheme_df['text'] == tmp_dtype, 'field'].iloc[0]

    # update plot with new inputs
    p = make_plot(input_field)

    # update layout, clear old document, create new document
    layout = column(p, Column(select_temp), Column(slider_yr), Column(select_mnth))
    
    # make use of wrapper column to add and remove layouts via
    # wrapper children attribute (children att is a glorified list)
    C.children = [layout]

    # new data for updated plot
    geosource.geojson = new_data


# create a plotting function
def make_plot(field_name):
    # define colorbar
    min_range = plt_scheme_df.loc[plt_scheme_df['field'] == field_name,
                                  'min_range'].iloc[0]
    max_range = plt_scheme_df.loc[plt_scheme_df['field'] == field_name, 'max_range'].iloc[0]
    field_format = plt_scheme_df.loc[plt_scheme_df['field'] == field_name, 'format'].iloc[0]

    # LinearColorMapper: num_range --> color sequence
    color_mapper = LinearColorMapper(palette=palette, low=min_range, high=max_range)

    # colorbar to help illustrate temperature
    format_tick = NumeralTickFormatter(format=field_format)
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=18,
                         formatter=format_tick, border_line_color=None,
                         major_label_text_color='grey',
                         location=(0, 0))

    # figure object
    text = plt_scheme_df.loc[plt_scheme_df['field'] == field_name, 'text'].iloc[0]

    p = figure(title = text + ' by California County - 2016 to 2020 (°F)',
               height=650, width=850,
               toolbar_location=None)

    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.axis.visible = False

    # render patch to figure: render map of California onto figure
    p.patches('xs', 'ys', source=geosource,
              fill_color={'field': field_name, 'transform': color_mapper},
              line_color='black', line_width=0.25, fill_alpha=1)

    # specify color bar layout
    p.add_layout(color_bar, 'right')

    # add the hover tool to the graph
    p.add_tools(hover)
    return p


# initial year 2020, month Jan, and weather data datatype TMAX
geosource = GeoJSONDataSource(geojson = json_wthr_data(2020, 1))
input_field = 'TMAX'

# color palette definition
palette = brewer['RdYlBu'][10]


# create hover tool
hover = HoverTool(tooltips = [ ('County', '@county'),
                               ('Maximum Temperature', '@TMAX'),
                               ('Minimum Temperature', '@TMIN')])

# top-level layout container
C = column()

# Call plotting function to generate figure
p = make_plot(input_field)

# slider_yr: Slider object to select views based on year
slider_yr = Slider(title='Year', start=2016, end=2020, step=1, value = 2020)
slider_yr.on_change('value', update_plot)

# select_temp: Select object to select views based on TMAX or TMIN
select_temp = Select(title = 'Temp Max/Min', value='Average Maximum Temperature',
                options=['Average Maximum Temperature', 'Average Minimum Temperature'])
select_temp.on_change('value', update_plot)

# select_mnth: Select object to select views based on month
select_mnth = Select(title="Month", value='Jan', options=list(month_abbr[1::]))
select_mnth.on_change('value', update_plot)

# make a column layout of plot and Column(widget_name) elements
layout = column(p, Column(select_temp), Column(slider_yr), Column(select_mnth))

# add this layout to the top-level container
C.children = [layout]

# display top-level container to the current document
curdoc().theme = Theme(filename=theme_pth)
curdoc().add_root(C)
