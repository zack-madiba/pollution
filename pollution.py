#_________récupéreration dans deux dictionnaires Python les données des deux polluants depuis les'APIs avec la bibliothèque requests______________________________________________________________________________________________________________________________________________________________________________________________________________________________________________
_
#!/usr/bin/env python3
# -*- coding: utf8 -*-

import psycopg2
from psycopg2.extensions import parse_dsn
import requests
import json
     
pm10 = requests.get('https://opendata.arcgis.com/datasets/08264f6574e844b8800ee0e18ca5ff9e_4.geojson')
dict_pm10 = pm10.json()
print(pm10.status_code)
     
no2 = requests.get('https://opendata.arcgis.com/datasets/08264f6574e844b8800ee0e18ca5ff9e_1.geojson')
dict_no2 = no2.json()
print(no2.status_code)
     
list_polluant = [dict_pm10, dict_no2]

#_____________________conexion postgresql et création des tables + integration données_________________________________________________________________________________________________________________________________________________________________________________________________________________
    
db_dsn = "postgres://postgres:test@localhost:5432/decouverte"
db_args = parse_dsn(db_dsn)
conn = psycopg2.connect(**db_args)
     
cur = conn.cursor()


     
cur.execute('''DROP TABLE IF EXISTS pollution''')
cur.execute('''CREATE TABLE IF NOT EXISTS pollution("departement" TEXT, "commune" TEXT, "insee_com" INT, "station" TEXT, "code_station" TEXT, "typologie" TEXT, "influence" TEXT, "polluant" VARCHAR(32), "id_poll_ue" INT, "valeur" FLOAT, "unite" TEXT, "date_debut" TIMESTAMP WITH TIME ZONE, "date_fin" TIMESTAMP WITH TIME ZONE, "longitude" FLOAT, "lattitude" FLOAT)''')
     
for polluant in list_polluant:
    for elt in polluant["features"]:
        val = []
        for i, v in elt["properties"].items():
            col = ['nom_dept', 'nom_com', 'insee_com', 'nom_station', 'code_station', 'typologie', 'influence', 'nom_poll','id_poll_ue', 'valeur', 'unite', 'date_debut', 'date_fin', 'x_wgs84','y_wgs84']
            if i in  col:
                val.append(v)
                #print(i, val)
    
        #print('\n')
        cur.execute("INSERT INTO pollution(departement, commune, insee_com, station, code_station, typologie, influence, polluant, id_poll_ue, valeur, unite, date_debut, date_fin, longitude, lattitude) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", val)

        
        
   
        
cur.execute('''DROP TABLE IF EXISTS departement cascade''')
cur.execute("""CREATE TABLE IF NOT EXISTS departement (
        "id_dept" SERIAL,
        "nom_dept" TEXT,
        PRIMARY KEY ("id_dept"));""")

cur.execute('''DROP TABLE IF EXISTS commune cascade''')
cur.execute("""CREATE TABLE IF NOT EXISTS commune (
        "id_commune" SERIAL, 
        "nom_com" TEXT,
        "insee_com" INTEGER,
        "departement_id_dept" INTEGER,
        PRIMARY KEY ("id_commune"),
        FOREIGN KEY ("departement_id_dept") REFERENCES departement ("id_dept"));""")
 
cur.execute('''DROP TABLE IF EXISTS polluants cascade''')
cur.execute("""CREATE TABLE IF NOT EXISTS polluants (
        "id" SERIAL,
        "nom_poll" TEXT,
        PRIMARY KEY ("id"));""")

cur.execute('''DROP TABLE IF EXISTS stations cascade''')
cur.execute("""CREATE TABLE IF NOT EXISTS stations(
        "id_station" SERIAL,
        "code_station" TEXT,
        "nom_station" TEXT,
        "longitude" FLOAT,
        "lattitude" FLOAT,
        "commune_id_commune" INTEGER,
        PRIMARY KEY ("id_station"),
        FOREIGN KEY ("commune_id_commune") REFERENCES commune ("id_commune"));""")

cur.execute('''DROP TABLE IF EXISTS Mesure_detectee cascade''')
cur.execute("""CREATE TABLE IF NOT EXISTS Mesure_detectee(
        "id_mesure" SERIAL,
        "stations_id_station" INTEGER,
        "polluants_id" INTEGER,
        "valeur" FLOAT,
        "unite" TEXT,
        "date_debut" TIMESTAMP WITH TIME ZONE,
        PRIMARY KEY ("id_mesure"),
        FOREIGN KEY ("stations_id_station") REFERENCES stations ("id_station"),
        FOREIGN KEY ("polluants_id") REFERENCES polluants ("id"));""")



##_______Insérertion des données dans les tables: departement, commune, polluants, stations, Mesure_detectee_____________

cur.execute ("""delete from departement""")
cur.execute("""INSERT INTO departement ("nom_dept")
    SELECT DISTINCT (departement)
    FROM pollution""") 

cur.execute ("""delete from commune""")
cur.execute("""INSERT INTO commune (nom_com, insee_com, departement_id_dept) 
    SELECT DISTINCT pollution.commune, pollution.insee_com, departement.id_dept
    FROM pollution
    join departement 
    on pollution.departement = departement.nom_dept;""")

cur.execute ("""delete from polluants""") 
cur.execute("""INSERT INTO polluants ("nom_poll") 
    SELECT DISTINCT (polluant)
    FROM pollution;""")

cur.execute ("""delete from stations""")
cur.execute("""INSERT INTO stations ("nom_station", "longitude", "lattitude", "code_station","commune_id_commune" ) 
    SELECT DISTINCT pollution.station, pollution.longitude, pollution.lattitude, pollution.code_station, commune.id_commune 
    FROM pollution
    JOIN commune
    ON pollution.commune = commune.nom_com;""")

cur.execute ("""delete from Mesure_detectee""")
cur.execute("""INSERT INTO Mesure_detectee ("stations_id_station", "polluants_id", "valeur", "unite", "date_debut" ) 
    SELECT stations.id_station, polluants.id, pollution.valeur, pollution.unite, pollution.date_debut
    FROM pollution
    JOIN stations
    ON pollution.station = stations.nom_station
    JOIN polluants
    ON pollution.polluant = polluants.nom_poll;""")




##_______________Creation de la table "pollution_final" + insertion des données dedans___________________________


cur.execute('''DROP TABLE IF EXISTS pollution_final''')
cur.execute(""" CREATE TABLE IF NOT EXISTS pollution_final 
( "departement_id_dept" INTEGER,
"commune_id_commune" INTEGER, 
"stations_id_station" INTEGER,
"polluants_id" INTEGER,
"mesure_detectee_id_mesure" INTEGER,
"typologie" TEXT,
"influence" TEXT,
"id_poll_ue" INTEGER,
"date_debut" TIMESTAMP WITH TIME ZONE,
FOREIGN KEY ("departement_id_dept") REFERENCES departement ("id_dept"), 
FOREIGN KEY ("commune_id_commune")  REFERENCES commune ("id_commune"), 
FOREIGN KEY ("stations_id_station") REFERENCES stations ("id_station"),
FOREIGN KEY ("polluants_id") REFERENCES polluants ("id"));""")


cur.execute ("""delete from pollution_final cascade""")
cur.execute(""INSERT INTO pollution_final (departement_id_dept, commune_id_commune, stations_id_station, polluants_id, mesure_detectee_id_mesure, typologie, influence, id_poll_ue, date_debut)
select departement.id_dept, commune.id_commune, stations.id_station, polluants.id, Mesure_detectee.id_mesure, pollution.typologie, pollution.influence, pollution.id_poll_ue, pollution.date_debut

from pollution

JOIN departement
ON pollutIon.departement = departement.nom_dept

JOIN commune
ON pollution.commune = commune.nom_com

JOIN stations
ON pollution.station = stations.nom_station

JOIN polluants
ON pollution.polluant = polluants.nom_poll

join Mesure_detectee 
on (stations.id_station, polluants.id, pollution.date_debut) = (Mesure_detectee.stations_id_station, Mesure_detectee.polluants_id, Mesure_detectee.date_debut);""")



        
            
conn.commit()
cur.close()
conn.close()


#_____________________________cartographie_______________________________________________________________________

import folium
ARA = [45.740858, 4.819629]

region = folium.Map(location = ARA, zoom_start = 7.5)

polluant = [dict_pm10["features"], dict_no2["features"]]

for element in dict_pm10["features"]:
    capteur = element["properties"]
    station = element['geometry']['coordinates']
    folium.Marker(location=[station[1],station[0]],popup = capteur["nom_station"]).add_to(region)
    
region
