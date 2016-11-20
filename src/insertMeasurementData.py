#!/usr/bin/python3

from sqlalchemy import create_engine
import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Date , func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
        

def insertMasspectrum(datafilename, experimenter, ionType )
        engine = create_engine('sqlite:///'+databaseName,echo=True)
	Base.metadata.bind = engine

	DBSession = sessionmaker(bind=engine)

	session=DBSession()

	names = [
	'Simon Dold',
	'Kiran Meier',
	'Fabian Bär',
	'Simon Dold',
	'Agigh Jaledoost']
	
	for name in names:
		new_data = Person(name=name)
		session.add(new_data)
		session.commit()

	clusterTypes = [
	['Silver','Ag',107.8682],
	['Gold','Au',196.96657]
	]
	
	for ct in clusterTypes:
		new_data = ClusterType(name=ct[0],clusterBaseUnit=ct[1],clusterBaseUnitMass=ct[2],)
		session.add(new_data)
		session.commit()


