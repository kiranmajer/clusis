#!/usr/bin/python3

from sqlalchemy import create_engine
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Date , func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
         

Base = declarative_base()
class Person(Base):
       __tablename__ = 'person'
       # Here we define columns for the table person
       # Notice that each column is also a normal Python instance attribute.
       id = Column(Integer, primary_key=True)
       name = Column(String(250), nullable=False)

class GeneralMeasurementData(Base):
        __tablename__='generalmeasurementdata'
        id = Column(Integer, primary_key=True)
        experimenter = Column(String(250), nullable=False)
        datatype     = Column(String(250), nullable=False)
        sha1         = Column(String(250), nullable=True)
        toolbox      = Column(String(250), nullable=True)
        datapath     = Column(String(250), nullable=False)
        date         = Column(Date, nullable=False, default=func.now())


class MassSpec(Base):
        __tablename__='massspectrum'

        id = Column(Integer, primary_key=True)
        comment = Column(String(250))
        dataset_id= Column(Integer, ForeignKey('generalmeasurementdata.id'))
        general_measurement_data = relationship(GeneralMeasurementData)
        tags      = Column(String(250), nullable=True)
        ionType      = Column(Integer, nullable=True)
        

class ClusterType(Base):
        __tablename__='clusterType'
        id = Column(Integer, primary_key=True)        
        name     = Column(String(250), nullable=False)
        clusterBaseUnit     = Column(String(250), nullable=False)
        clusterBaseUnitMass     = Column(Integer,nullable=False)


