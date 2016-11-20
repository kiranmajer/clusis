from dbClasses import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker



def createDatabase(databaseName = 'measurementdata.db'):

	engine = create_engine('sqlite:///'+databaseName,echo=True)

	Base.metadata.create_all(engine)

def insertRequiredData(databaseName = 'measurementdata.db'):
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


