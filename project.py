from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, FoodTruck, MenuItem, User
from flask import session as login_session
from flask import make_response, jsonify, url_for, flash
from flask import Flask, render_template, request, redirect, g
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from functools import wraps
import requests
import httplib2
import json
import random
import string


app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Food Truck Menu Application"

engine = create_engine('sqlite:///food_truck_database.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create a state token to prevent request forgery.
# Store it in the session for later validation


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        credentials = login_session.get('credentials')
        if credentials is None:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(
        string.ascii_uppercase + string.digits
        ) for x in xrange(32))
    login_session['state'] = state
    # return state
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """ CONNECT:

    Use Oauth to allow the user to login with Google account """

    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = request.args.get('gplus_id')
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps(
            'Failed to upgrade the authorization code.'
            ), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = (
        'https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
            'Current user is already connected.'
            ), 200)
        response.headers['Content-Type'] = 'application/json'

    # Store the access token in the session for later use.
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
    response = make_response(json.dumps('Successfully connected user.', 200))

    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)
    data = json.loads(answer.text)

    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id
    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 100px; height: \
        100px;border-radius: 50px;\
        -webkit-border-radius:\
        50px;-moz-border-radius: 50px;"> '

    flash("you are now logged in as %s" % login_session['username'])
    return output


@app.route("/gdisconnect")
def gdisconnect():
    """ DISCONNECT:

    Revoke a current user's token and reset their login_session.
    Only disconnect a connected user.

    """
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps(
            'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(json.dumps(
            'Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Food Truck Information
@app.route('/food_truck/<int:food_truck_id>/menu/JSON')
def food_truckMenuJSON(food_truck_id):
    food_truck = session.query(FoodTruck).filter_by(id=food_truck_id).one()
    items = session.query(MenuItem).filter_by(
        food_truck_id=food_truck_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/food_truck/<int:food_truck_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(food_truck_id, menu_id):
    Menu_Item = session.query(MenuItem).filter_by(id=menu_id).one()
    return jsonify(Menu_Item=Menu_Item.serialize)


@app.route('/food_truck/JSON')
def food_trucksJSON():
    food_trucks = session.query(FoodTruck).all()
    return jsonify(food_trucks=[r.serialize for r in food_trucks])


@app.route('/')
@app.route('/food_truck/')
def showFoodTrucks():
    """ Show all food trucks """

    food_trucks = session.query(FoodTruck).order_by(asc(FoodTruck.name))
    credentials = login_session.get('credentials')
    return render_template(
        'food_trucks.html',
        food_trucks=food_trucks,
        credentials=credentials)


@app.route('/food_truck/new/', methods=['GET', 'POST'])
@login_required
def newFoodTruck():
    """ Create a new food truck """

    credentials = login_session.get('credentials')

    if request.method == 'POST':
        login_user_id = getUserID(login_session['email'])
        newFoodTruck = FoodTruck(
            name=request.form['name'], user_id=login_user_id)
        session.add(newFoodTruck)
        flash('New Food Truck %s Successfully Created' % newFoodTruck.name)
        session.commit()
        return redirect(url_for('showFoodTrucks'))
    else:
        return render_template(
            'newFoodTruck.html', credentials=credentials)


@app.route('/food_truck/<int:food_truck_id>/edit/', methods=['GET', 'POST'])
@login_required
def editFoodTruck(food_truck_id):
    """ Edit a food Truck """

    credentials = login_session.get('credentials')

    editedFoodTruck = session.query(FoodTruck).filter_by(
        id=food_truck_id).one()
    if 'username' not in login_session:
        return redirect('/login')
    if editedFoodTruck.user_id != login_session['user_id']:
        return "<script>function myFunction() \
            {alert('You are not authorized to \
            edit this food truck. Please create \
            your own food truck in order to edit.');}\
            </script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedFoodTruck.name = request.form['name']
            flash('Food Truck Successfully Edited %s' % editedFoodTruck.name)
            session.add(editedFoodTruck)
            session.commit()
            return redirect(url_for('showFoodTrucks'))
    else:
        return render_template(
            'editFoodTruck.html',
            food_truck=editedFoodTruck,
            credentials=credentials)


@app.route('/food_truck/<int:food_truck_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteFoodTruck(food_truck_id):
    """ Delete a food_truck """

    credentials = login_session.get('credentials')
    food_truckToDelete = session.query(FoodTruck).filter_by(
        id=food_truck_id).one()

    if request.method == 'POST':
        session.delete(food_truckToDelete)
        # also delete menu items from the truck being deleted:
        session.query(MenuItem).filter_by(food_truck_id=food_truck_id).delete()
        flash('%s Successfully Deleted' % food_truckToDelete.name)
        session.commit()
        return redirect(url_for(
            'showFoodTrucks', food_truck_id=food_truck_id))
    else:
        return render_template(
            'deleteFoodTruck.html',
            food_truck=food_truckToDelete,
            credentials=credentials)
        return redirect(url_for(
            'showFoodTrucks',
            food_truck_id=food_truck_id,
            credentials=credentials))


@app.route('/food_truck/<int:food_truck_id>/')
@app.route('/food_truck/<int:food_truck_id>/menu/')
def showMenu(food_truck_id):
    items = session.query(MenuItem).filter_by(
        food_truck_id=food_truck_id).all()
    """ Show a food_truck menu """

    food_truck = session.query(FoodTruck).filter_by(id=food_truck_id).one()
    creator_id = food_truck.user_id
    creator_user = session.query(User).filter_by(id=creator_id).one()
    creator_name = creator_user.name
    creator_picture = creator_user.picture
    credentials = login_session.get('credentials')

    if credentials is None:
        login_user_id = 0
    else:
        login_user_id = getUserID(login_session['email'])

    return render_template(
        'menu.html', items=items, food_truck=food_truck,
        creator_name=creator_name, creator_picture=creator_picture,
        login_user_id=login_user_id, credentials=credentials,
        creator_id=creator_id)


@app.route(
    '/food_truck/<int:food_truck_id>/menu/new/',
    methods=['GET', 'POST'])
@login_required
def newMenuItem(food_truck_id):
    """ Create a new menu item """

    credentials = login_session.get('credentials')
    if 'username' not in login_session:
        return redirect('/login')
    food_truck = session.query(FoodTruck).filter_by(id=food_truck_id).one()

    if login_session['user_id'] != food_truck.user_id:
        return "<script>function myFunction() {alert( \
        'You are not authorized to add menu items to this \
        food truck. Please create your own food truck in \
        order to add items.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        newItem = MenuItem(
            name=request.form['name'],
            description=request.form['description'],
            price=request.form['price'],
            course=request.form['course'],
            food_truck_id=food_truck_id,
            user_id=food_truck.user_id)
        session.add(newItem)
        session.commit()
        flash('New Menu %s Item Successfully Created' % (newItem.name))
        return redirect(url_for(
            'showMenu',
            food_truck_id=food_truck_id))
    else:
        return render_template(
            'newmenuitem.html',
            food_truck_id=food_truck_id, credentials=credentials)


@app.route(
    '/food_truck/<int:food_truck_id>/menu/<int:menu_id>/edit',
    methods=['GET', 'POST'])
@login_required
def editMenuItem(food_truck_id, menu_id):
    """ Edit a menu item """

    credentials = login_session.get('credentials')
    if credentials is None:
        login_status = "not logged in"
        login_user_id = 0
        login_username = "no username"
    else:
        login_status = "logged in"
        login_user_id = getUserID(login_session['email'])
        login_username = login_session['username']

    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(MenuItem).filter_by(id=menu_id).one()
    food_truck = session.query(FoodTruck).filter_by(id=food_truck_id).one()
    if login_session['user_id'] != food_truck.user_id:
        return "<script>function myFunction() {alert(\
        'You are not authorized to edit menu items to\
        this restaurant. Please create your own restaurant\
        in order to edit items.');}</script>\
        <body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if request.form['course']:
            editedItem.course = request.form['course']
        session.add(editedItem)
        session.commit()
        flash('Menu Item Successfully Edited')
        return redirect(url_for(
            'showMenu',
            food_truck_id=food_truck_id))
        return render_template(
            'editmenuitem.html',
            food_truck_id=food_truck_id,
            menu_id=menu_id, credentials=credentials,
            item=editedItem)


@app.route(
    '/food_truck/<int:food_truck_id>/menu/<int:menu_id>/delete',
    methods=['GET', 'POST'])
@login_required
def deleteMenuItem(food_truck_id, menu_id):
    """ Delete a menu item """

    credentials = login_session.get('credentials')
    if credentials is None:
        login_status = "not logged in"
        login_user_id = 0
        login_username = "no username"
    else:
        login_status = "logged in"
        login_user_id = getUserID(login_session['email'])
        login_username = login_session['username']

    food_truck = session.query(FoodTruck).filter_by(id=food_truck_id).one()
    itemToDelete = session.query(MenuItem).filter_by(id=menu_id).one()

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Menu Item Successfully Deleted')
        return redirect(url_for(
            'showMenu',
            food_truck_id=food_truck_id))
    else:
        return render_template(
            'deleteMenuItem.html',
            item=itemToDelete,
            login_status=login_status,
            login_username=login_username,
            food_truck=food_truck, credentials=credentials)


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
