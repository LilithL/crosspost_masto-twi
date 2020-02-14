import os
import sys

from datetime import datetime
from sqlalchemy import Column, DateTime, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class Crossposted_toots(Base):
    __tablename__ = "crossposted_toots"
    user_id = Column(String(100), primary_key=True)
    toot_id = Column(String(100), primary_key=True)
    tweet_id = Column(String(100))
    date = Column(DateTime)


def init(db_file):
    engine = create_engine('sqlite:///'+db_file)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


class Session_db:
    def __init__(self, db_file):
        self.engine = create_engine('sqlite:///'+db_file)
        Base.metadata.bind = self.engine
        DBSession = sessionmaker(bind=self.engine)
        self.session = DBSession()


    def crossposted_object(self, user_id, toot_id, tweet_id):
        return Crossposted_toots(user_id=str(user_id), toot_id=str(toot_id), tweet_id=str(tweet_id), date=datetime.today())

    def add_toot(self, user_id, toot_id, tweet_id):
        self.session.add(self.crossposted_object(user_id, toot_id, tweet_id))
        self.session.commit()
    
    def get_last_toot(self, user_id):
        try:
            return self.session.query(Crossposted_toots).filter_by(user_id=str(user_id)).order_by(Crossposted_toots.date.desc()).first()
        except Exception as e:
            print(e)
            return None
    
    def get_tweet_id(self, toot_id):
        if toot_id == None:
            return None
        try:
            return self.session.query(Crossposted_toots).filter_by(toot_id=str(toot_id)).first().tweet_id
        except Exception as e:
            print(e)
            return None