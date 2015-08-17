import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database

engine = create_engine("postgres://localhost/mydb")
if not database_exists(engine.url):
	create_database(engine.url)

print(database_exists(engine.url)




#Base = declarative_base()


class User(Base):
    __tablename__ = 'user_list'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))


class FoodTruck(Base):
    __tablename__ = 'food_truck'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer, ForeignKey('user_list.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
           'name': self.name,
           'id': self.id,
           }


class MenuItem(Base):
    __tablename__ = 'menu_item'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250))
    price = Column(String(8))
    course = Column(String(250))
    food_truck_id = Column(Integer, ForeignKey('food_truck.id'))
    food_truck = relationship(FoodTruck)
    user_id = Column(Integer, ForeignKey('user_list.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'description': self.description,
            'id': self.id,
            'price': self.price,
            'course': self.course,
            }

#engine = create_engine('postgresql://postgres:postgres@52.24.210.121:80/food_truck_db')

Base.metadata.create_all(engine)
