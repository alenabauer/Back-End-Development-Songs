from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.route("/health")
def health():
    return jsonify(dict(status="OK")), 200

@app.route("/count")
def count():
    """return length of data"""
    count = db.songs.count_documents({})
    if count:
        return jsonify(count=count), 200

    return {"message": "Internal server error"}, 500

@app.route("/song", methods=["GET"])
def get_songs():
    """return all songs"""
    songs = db.songs.find({})
    if songs:
        return jsonify(songs=parse_json(songs)), 200

    return {"message": "Internal server error"}, 500

@app.route("/song/<int:id>", methods=["GET"])
def get_song(id):
    """return a song"""
    song = db.songs.find_one({"id": id})

    if song:
        return jsonify(song=parse_json(song)), 200

    return {"message": "Song not found"}, 404

@app.route("/song", methods=["POST"])
def create_song():
    """create a song"""
    data = request.get_json()
    if not data:
        return {"message": "Missing data"}, 400

    song = db.songs.find_one({"id": data["id"]})
    if song:
        return {"Message": "song with id {} already present".format(data["id"])}, 302

    result: InsertOneResult = db.songs.insert_one(data)
    if result:
        return jsonify(song=parse_json(data)), 201

    return {"message": "Internal server error"}, 500

@app.route("/song/<int:id>", methods=["PUT"])
def update_song(id):
    """update a song"""
    data = request.get_json()
    if not data:
        return {"message": "Missing data"}, 400

    song = db.songs.find_one({"id": id})
    if not song:
        return {"message": "Song not found"}, 404

    result = db.songs.update_one({"id": id}, {"$set": data})
    if result:
        return jsonify(song=parse_json(data)), 200

    return {"message": "Internal server error"}, 500

@app.route("/song/<int:id>", methods=["DELETE"])
def delete_song(id):
    """delete a song"""
    song = db.songs.find_one({"id": id})
    if not song:
        return {"message": "Song not found"}, 404

    result = db.songs.delete_one({"id": id})
    if result:
        return {}, 204

    return {"message": "Internal server error"}, 500