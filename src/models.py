from typing import Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime,Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
import datetime

db = SQLAlchemy()


class User(db.Model):
    
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    subscription_data: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user")
    
    def serialize(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "last_name": self.last_name,
            "email": self.email,
            "subscription_data": self.subscription_data.isoformat()
        }
    
class Planet(db.Model):
    
    __tablename__ = 'planets'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    weather: Mapped[str] = mapped_column(String(100))
    population: Mapped[int] = mapped_column(Integer)
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="planet")
    
    def serialize(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "weather": self.weather,
            "population": self.population
        }

class People(db.Model):
    
    __tablename__ = 'peoples'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    birth: Mapped[Optional[str]] = mapped_column(String(20))
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="people")
    
    def serialize(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "gender": self.gender,
            "birth": self.birth
        }

class Favorite(db.Model):
    
    __tablename__ = 'favorite'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    planet_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('planets.id'), nullable=True)
    people_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('peoples.id'), nullable=True)
    user: Mapped["User"] = relationship(back_populates="favorites")
    planet: Mapped[Optional["Planet"]] = relationship(back_populates="favorites")
    people: Mapped[Optional["People"]] = relationship(back_populates="favorites")
    
    def serialize(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "planet_id": self.planet_id,
            "people_id": self.people_id
        }