import random
import time

import api
import googlemaps
from flask import Flask, render_template, redirect, url_for, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///search_list.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Create database


class SearchList(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

# db.create_all()

# Using google api to search


def search_google(search_string, radius):
    # Api key import from api.py file for github to not show security warning
    api_key = api.API_KEY
    map_client = googlemaps.Client(api_key)
    # finding current location
    current = map_client.geolocate()
    # Parameters
    location = (current['location']['lat'], current['location']['lng'])
    search_string = search_string
    distance = radius
    # init list to store response data
    response_list = []
    # calling google API
    response = map_client.places_nearby(
        location=location,
        keyword=search_string,
        radius=distance,)
    response_list.extend(response.get('results'))
    next_page_token = response.get('next_page_token')
    while next_page_token:
        # if request is too fast there is a chance we will get duplicate results
        time.sleep(2)
        response = map_client.places_nearby(
            location=location,
            keyword=search_string,
            name='petrol',
            radius=distance,
            page_token=next_page_token,)
        response_list.extend(response.get('results'))

        next_page_token = response.get('next_page_token')
    return response_list


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == "POST":

        # need to delete data in database before calling google api 
        db.session.query(SearchList).delete()
        keyword = request.form['search']
        distance = request.form['distance']
        response_list = search_google(keyword, distance)
        for item in response_list:
            new_data = SearchList(
                name=item['name'],
                rating=item['rating'],
                address=item['vicinity']
            )
            db.session.add(new_data)
        db.session.commit()

        data_list = db.session.query(SearchList).all()

        return render_template('index.html', data_list=data_list)

    return(render_template('index.html'))

@app.route('/api_request')
def api_request():
    places = db.session.query(SearchList).first()
    if places:
        return jsonify(places.to_dict())
    else:
        return jsonify(error={'Not found':'Database is empty'})


if __name__ == "__main__":
    app.run(debug=True)
