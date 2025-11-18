"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, People, Favorite


app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)



#-----------------------------------User, Favorites----------------------------
@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()

    name = data.get('name')
    last_name = data.get('last_name')
    email = data.get('email')
    password = data.get('password')
    
    if not name:
        return jsonify({"error": "The field name is required"}), 400
    if not last_name:
        return jsonify({"error": "The field last name is required"}), 400
    if not email:
        return jsonify({"error": "The field email is required"}), 400
    if not password:
        return jsonify({"error": "The field pasword is required"}), 400

    user_exists = User.query.filter_by(email=email).first()
    if user_exists:
        return jsonify({"error": "User already exist"}), 400

    new_user = User(
        name=name,
        last_name=last_name,
        email=email,
        password=password
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully", "user": new_user.serialize()}), 201



@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    users_serialized = [user.serialize() for user in users]
    
    if users_serialized:
        return jsonify(users_serialized), 200
    else:
        return jsonify({"message": "No Users exists"}), 404
    



@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Missing user_id "}), 400
    
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id must be a number"}), 400
    
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
   
    favorites = Favorite.query.filter_by(user_id=user_id).all()
    
    if not favorites:
        return jsonify({"message": "Not favorites yet"}), 404
    
    result = []
    for fav in favorites:
        if fav.planet_id and fav.planet:
            result.append({
                "id": fav.id,
                "type": "planet",
                "planet": fav.planet.serialize()
            })
        elif fav.people_id and fav.people:
            result.append({
                "id": fav.id,
                "type": "people",
                "people": fav.people.serialize()
            })
    
    return jsonify(result), 200



@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Missing user_id"}), 400
    
    # Convertir user_id a entero y validar
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id must be a number"}), 400
    
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"message": "ID from Planet not found"}), 404
    
    
    favorite_exist = Favorite.query.filter_by(
        user_id=user_id, 
        planet_id=planet_id
    ).first()
    
    if favorite_exist:
        return jsonify({"message": "Planet not in favorite anymore"}), 409
    
    
    new_favorite = Favorite(
        user_id=user_id,
        planet_id=planet_id,
        people_id=None  
    )
    
    
    db.session.add(new_favorite)
    db.session.commit()
    
    return jsonify({
        "message": "Planet added to favorites ",
        "favorite": new_favorite.serialize()
    }), 201
    

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "missing user_id en query"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id must be a number"}), 400
    
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
   
    people = People.query.get(people_id)
    if not people:
        return jsonify({"message": "ID from people not found"}), 404
    
    
    favorite_exist = Favorite.query.filter_by(
        user_id=user_id, 
        people_id=people_id
    ).first()
    
    if favorite_exist:
        return jsonify({"message": "People already added to favorite"}), 409
    
    
    new_favorite = Favorite(
        user_id=user_id,
        planet_id=None,  # Solo personaje, no planeta
        people_id=people_id
    )
    
    
    db.session.add(new_favorite)
    db.session.commit()
    

    return jsonify({
        "message": "People added to favorite",
        "favorite": new_favorite.serialize()
    }), 201
    
@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Missing user_id"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id must be a number"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
   
    favorite = Favorite.query.filter_by(
        user_id=user_id, 
        planet_id=planet_id
    ).first()
    
    if not favorite:
        return jsonify({"message": "Favorite from planet not found in this user"}), 404
    
    
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Planet deleted from favorites"}), 200


@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(people_id):
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"message": "Missing user_id"}), 400
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({"message": "user_id must be a number"}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    favorite = Favorite.query.filter_by(
        user_id=user_id, 
        people_id=people_id
    ).first()
    
    if not favorite:
        return jsonify({"message": "Favorite from people not found from this user"}), 404
    
    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "People deleted from favorite"}), 200


#-----------------------------------Planets--------------------------------------------

@app.route('/planets', methods=['POST'])
def create_planet():
    data = request.get_json()
    name = data.get('name')
    weather = data.get('weather')
    population = data.get('population')
    if not name:
        return jsonify({"message": "Name required"}), 400
    new_planet = Planet(name=name, weather=weather, population=population)
    db.session.add(new_planet)
    db.session.commit()
    return jsonify({"message":"Planet created"},new_planet.serialize()), 201

@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    planets_serialized = [planet.serialize() for planet in planets]
    if planets_serialized:
        return jsonify(planets_serialized), 200
    else:
        return jsonify({"message": "No existed planetes"}), 404


@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_planet_by_id(planet_id):
    planet = Planet.query.get(planet_id)
    if planet:
        return jsonify(planet.serialize()), 200
    else:
        return jsonify({"message": "ID de Planet no found"}), 404



#-------------------------People----------------------
@app.route('/people', methods=['POST'])
def create_person():
    data = request.get_json()
    name = data.get('name')
    gender = data.get('gender')
    birth = data.get('birth')
    if not name:
        return jsonify({"message": "Name is required"}), 400
    new_people = People(name=name, gender=gender, birth=birth)
    db.session.add(new_people)
    db.session.commit()
    return jsonify({"message": "People created"}, new_people.serialize()), 201



@app.route('/people', methods=['GET'])
def get_all_people():
    people = People.query.all()
    peoples_serialized = [peoples.serialize() for peoples in people]
    
    if peoples_serialized:
        return jsonify(peoples_serialized), 200
    else:
        return jsonify({"message": "No exisiting people"}), 404


@app.route('/people/<int:people_id>', methods=['GET'])
def get_person_by_id(people_id):
    people = People.query.get(people_id)
    if people:
        return jsonify(people.serialize()), 200
    else:
        return jsonify({"message": "ID from people not found"}), 404



# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
