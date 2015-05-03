from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import FoodTruck, Base, MenuItem, User

engine = create_engine('sqlite:///food_truck_database.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()

# Delete previous users
all_users = session.query(User).all()
for i in all_users:
    session.delete(i)
session.commit()

# Delete previous food_trucks
all_food_trucks = session.query(FoodTruck).all()
for i in all_food_trucks:
    session.delete(i)
session.commit()

# Delete previous menu items
all_menu_items = session.query(MenuItem).all()
for i in all_menu_items:
    session.delete(i)
session.commit()


# Create test users
user1 = User(name = "Jovencio Rabe", email="jovenciorabe@gmail.com", picture="https://lh3.googleusercontent.com/-XdUIqdMkCWA/AAAAAAAAAAI/AAAAAAAAAAA/4252rscbv5M/photo.jpg")
session.add(user1)
session.commit()

user2 = User(name = "Ana Leda Rabe", email="analeda13460@gmail.com", picture="https://lh3.googleusercontent.com/-XdUIqdMkCWA/AAAAAAAAAAI/AAAAAAAAAAA/4252rscbv5M/photo.jpg")
session.add(user2)
session.commit()

user3 = User(name = "Evan Wappel", email="ewappel@gmail.com", picture="https://lh3.googleusercontent.com/-XdUIqdMkCWA/AAAAAAAAAAI/AAAAAAAAAAA/4252rscbv5M/photo.jpg")
session.add(user3)
session.commit()

#

# Jovencio's food truck (Chairman)

food_truck1 = FoodTruck(name = "Jovencio's Food Truck", user_id_database=1)
session.add(food_truck1)
session.commit()

menuItem1 = MenuItem(name = "Tender Pork Belly with Turmeric Pickled Daikon & Green Shiso", description = "tasty traditional Taiwanese snack", price = "$3.75", course = "Appetizer", food_truck = food_truck1, user_id_database=1)
session.add(menuItem1)
session.commit()

menuItem2 = MenuItem(name = "ADOBO", description = "the chef's famous adobo", price = "$8.50", course = "Entree", food_truck = food_truck1, user_id_database=1)
session.add(menuItem2)
session.commit()

menuItem3 = MenuItem(name = "BUKO PIE", description = "coconut pie", price = "$6", course = "Dessert", food_truck = food_truck1, user_id_database=1)
session.add(menuItem3)
session.commit()

menuItem4 = MenuItem(name = "ROMBAUER CHARDONNAY", description = "premium wine", price = "$7", course = "Beverage", food_truck = food_truck1, user_id_database=1)
session.add(menuItem4)
session.commit()


# Leda's food truck (Kogi)
food_truck2 = FoodTruck(name = "Leda's Food Truck", user_id_database=2)
session.add(food_truck2)
session.commit()

menuItem1 = MenuItem(name = "FRESH SPRING ROLLS", description = "with peanut sauce", price = "$4.95", course = "Appetizer", food_truck = food_truck2, user_id_database=2)
session.add(menuItem1)
session.commit()

menuItem2 = MenuItem(name = "VERMICELLI NOODLES", description = "house special", price = "$8.95", course = "Entree", food_truck = food_truck2, user_id_database=2)
session.add(menuItem2)
session.commit()

menuItem3 = MenuItem(name = "CREME BRULEE", description = "with strawberries", price = "$7", course = "Dessert", food_truck = food_truck2, user_id_database=2)
session.add(menuItem3)
session.commit()

menuItem4 = MenuItem(name = "GAMAY ROUGE", description = "sweet red wine", price = "$6", course = "Beverage", food_truck = food_truck2, user_id_database=2)
session.add(menuItem4)
session.commit()




# Evan's food truck (Opie's)
food_truck3 = FoodTruck(name = "Evan's Food Truck", user_id_database=3)
session.add(food_truck3)
session.commit()

menuItem1 = MenuItem(name = "NACHOS & SALSA", description = "spicy salsa", price = "$4.50", course = "Appetizer", food_truck = food_truck3, user_id_database=3)
session.add(menuItem1)
session.commit()

menuItem2 = MenuItem(name = "ENCHILADAS", description = "special sauce", price = "$7.95", course = "Entree", food_truck = food_truck3, user_id_database=3)
session.add(menuItem2)
session.commit()

menuItem3 = MenuItem(name = "CHOCOLATE CAKE", description = "with ice cream", price = "$5", course = "Dessert", food_truck = food_truck3, user_id_database=3)
session.add(menuItem3)
session.commit()

menuItem4 = MenuItem(name = "MEXICAN HOT CHOCOLATE", description = "with cinnamon", price = "$5", course = "Beverage", food_truck = food_truck3, user_id_database=3)
session.add(menuItem4)
session.commit()


#  Example food truck (El Jefe)

food_truck4 = FoodTruck(name = "Example Food Truck")
session.add(food_truck4)
session.commit()

menuItem1 = MenuItem(name = "CALAMARI", description = "with garlic and parmesan", price = "$4.95", course = "Appetizer", food_truck = food_truck4)
session.add(menuItem1)
session.commit()

menuItem2 = MenuItem(name = "ADOBO", description = "the chef's famous adobo", price = "$8.50", course = "Entree", food_truck = food_truck4)
session.add(menuItem2)
session.commit()

menuItem3 = MenuItem(name = "BUKO PIE", description = "coconut pie", price = "$6", course = "Dessert", food_truck = food_truck4)
session.add(menuItem3)
session.commit()

menuItem4 = MenuItem(name = "ROMBAUER CHARDONNAY", description = "premium wine", price = "$7", course = "Beverage", food_truck = food_truck4)
session.add(menuItem4)
session.commit()



print "added menu items!"
