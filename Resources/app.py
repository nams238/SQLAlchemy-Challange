from optparse import Values
from unicodedata import name
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.sql import exists
from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///activities/Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
Measurement = Base.classes.measurement
Station = Base.classes.station
#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start (enter as YYYY-MM-DD)<br/>"
        f"/api/v1.0/start/end (enter as YYYY_MM_DD)<br/>"
    )
#Convert the query results to a dictionary using 'date' as the key and 'prcp' as the value.
@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)

    #Query Measurement
    values = (session.query(Measurement.date, Measurement.tobs)
        .order_by(Measurement.date))
    

    # create a dictionary
    precipitation_date_prcp = []
    for value in values:
        row = {}
        row["date"] = value[0]
        row["prcp"] = float(value[1])
        precipitation_date_prcp.append(row)

    return jsonify(precipitation_date_prcp)


#Return a JSON list of stations from the dataset.
@app.route("/api/v1.0/stations")
def stations():
    # create a link from python to the database
    session = Session(engine)

    # Query all stations
    values = session.query(Station.name).all()

    # convert list of tuple into normal list
    all_stations = list(np.ravel(values))

    return jsonify(all_stations)


#Query the dates and temperature observations of the most active station for the previous year of data.
@app.route("/api/v1.0/tobs")
def tobs():
    # create a session link from python to the database
    session = Session(engine)

    # Query station names and do a station count to get the most active
    station_list = (session.query(Measurement.station, func.count(Measurement.station))
        .group_by(Measurement.station)
        .order_by(func.count(Measurement.station).desc())
        .all())

    most_active = station_list[0][0]
    print(most_active)

    # Return a list of temperature (tobs) for the previous year
    values = (session.query(Measurement.station, Measurement.date, Measurement.tobs)
            .filter(Measurement.date >= '2016-08-23')
            .filter(Measurement.station == most_active)
            .all())

    # create JSON list
    tobs_values = []
    for value in values:
        row = {}
        row["Station"] = value[0]
        row["Date"] = value[1]
        row["Temperature"] = int(value[2])
        tobs_values.append(row)

    return jsonify(tobs_values)


# calculate TMIN, TAVG, and TMAX for all dates greater than or equal to the start date
@app.route("/api/v1.0/<start>")
def star_only(start):
    # create link from python to database
    session = Session(engine)

    # check for valid valid date entry
    valid_date = session.query(exists().where(Measurement.date == start)).scalar()

    if valid_date:
        values = (session.query(func.min(Measurement.tobs)
            ,func.max(Measurement.tobs)
            ,func.avg(Measurement.tobs))
            .filter(Measurement.date >=start).all())

        tmin = values[0][0]
        tmax = values[0][1]
        tavg = '{0:.4}'.format(values[0][2])

        values_output = (['Entered Start Date:' + start, 
                                    'Lowest Temperature: ' + str(tmin) + 'F',
                                    'Highest Temperature: ' + str(tmax) + 'F',
                                    'Average Temperature: ' + str(tavg) + 'F'])

        return jsonify(values_output)               
    
    return jsonify({"error": f"Input Date {start} not valid. Enter a valid date"}), 404


#calculate the TMIN, TAVG, and TMAX for dates from the start date through the end date (inclusive).
@app.route("/api/v1.0/<start>/<end>")
def start_end(start, end):
    # create a session link from Python to the database
    session = Session(engine)

    # check that start date is valid
    valid_start_date = session.query(exists().where(Measurement.date == start)).scalar()

    # check that start date is valid
    valid_end_date = session.query(exists().where(Measurement.date == end)).scalar()

    if valid_start_date and valid_end_date:

        values = (session.query(func.min(Measurement.tobs),func.max(Measurement.tobs)
                                    ,func.avg(Measurement.tobs))
                                    .filter(Measurement.date >= start)
                                    .filter(Measurement.date <= end).all())


        tmin = values[0][0]
        tmax = values[0][1]
        tavg = '{0:.4}'.format(values[0][2])

        values_output = (['Entered Start Date:' + start, 
                                        'Entered End Date: ' + end,
                                        'Lowest Temperature: ' + str(tmin) + 'F',
                                        'Highest Temperature: ' + str(tmax) + 'F',
                                        'Average Temperature: ' + str(tavg) + 'F'])

        return jsonify(values_output)               
        


    if not valid_start_date and not valid_end_date:

        return jsonify({"error": f"Input Start Date {start} and  End Date {end} not valid. Enter a valid date"}), 404

if __name__ == '__main__':
    app.run(debug=True)