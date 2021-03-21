import psycopg2
from psycopg2.extensions import parse_dsn
import requests
import json
import folium
#_________________________________collecte de données_______________________________________________
     
pm10 = requests.get('https://opendata.arcgis.com/datasets/08264f6574e844b8800ee0e18ca5ff9e_4.geojson')
dict_pm10 = pm10.json()
print(pm10.status_code)
     
no2 = requests.get('https://opendata.arcgis.com/datasets/08264f6574e844b8800ee0e18ca5ff9e_1.geojson')
dict_no2 = no2.json()
print(no2.status_code)
     
list_polluant = [dict_pm10, dict_no2]

#_____________________________________________creation de la base de données en postgresql___________________
     
db_dsn = "postgres://postgres:test@localhost:5432/decouverte"
db_args = parse_dsn(db_dsn)
conn = psycopg2.connect(**db_args)
     
cur = conn.cursor()
     
cur.execute('''DROP TABLE IF EXISTS pollution''')
cur.execute('''CREATE TABLE IF NOT EXISTS pollution("departement" TEXT, "commune" TEXT, "insee_com" INT, "station" TEXT, "code_station" TEXT, "typologie" TEXT, "influence" TEXT, "polluant" VARCHAR(32), "id_poll_ue" INT, "valeur" FLOAT, "unite" TEXT, "date_debut" TIMESTAMP WITH TIME ZONE, "date_fin" TIMESTAMP WITH TIME ZONE, "longitude" FLOAT, "latitude" FLOAT)''')
     
for polluant in list_polluant:
    for elt in polluant["features"]:
        val = []
        for i, v in elt["properties"].items():
            col = ['nom_dept', 'nom_com', 'insee_com', 'nom_station', 'code_station', 'typologie', 'influence', 'nom_poll','id_poll_ue', 'valeur', 'unite', 'date_debut', 'date_fin', 'x_wgs84','y_wgs84']
            if i in  col:
                val.append(v)
                print(i, val)
   
        print('\n')
        cur.execute("INSERT INTO pollution(departement, commune, insee_com, station, code_station, typologie, influence, polluant, id_poll_ue, valeur, unite, date_debut, date_fin, longitude, latitude) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", val)
 
       
       
#____________________________ Créer les tables secondaires________________________________________________________
     
       
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
        "latitude" FLOAT,
        "commune_id_commune" INTEGER,
        PRIMARY KEY ("id_station"),
        FOREIGN KEY ("commune_id_commune") REFERENCES commune ("id_commune"));""")
 
cur.execute('''DROP TABLE IF EXISTS Mesure cascade''')
cur.execute("""CREATE TABLE IF NOT EXISTS Mesure(
        "id_mesure" SERIAL,
        "stations_id_station" INTEGER,
        "polluants_id" INTEGER,
        "valeur" FLOAT,
        "unite" TEXT,
        "date_debut" TIMESTAMP WITH TIME ZONE,
        PRIMARY KEY ("id_mesure"),
        FOREIGN KEY ("stations_id_station") REFERENCES stations ("id_station"),
        FOREIGN KEY ("polluants_id") REFERENCES polluants ("id"));""")
 
 
 
#____________________________________________Insérer des données dans les tables secondaires respectives_________________
 
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
cur.execute("""INSERT INTO stations ("nom_station", "longitude", "latitude", "code_station","commune_id_commune" )
    SELECT DISTINCT pollution.station, pollution.longitude, pollution.latitude, pollution.code_station, commune.id_commune
    FROM pollution
    JOIN commune
    ON pollution.commune = commune.nom_com;""")
 
cur.execute ("""delete from Mesure""")
cur.execute("""INSERT INTO Mesure ("stations_id_station", "polluants_id", "valeur", "unite", "date_debut" )
    SELECT stations.id_station, polluants.id, pollution.valeur, pollution.unite, pollution.date_debut
    FROM pollution
    JOIN stations
    ON pollution.station = stations.nom_station
    JOIN polluants
    ON pollution.polluant = polluants.nom_poll;""")
 
 
 
#_______________________________________________________creation table pollution_2 ____________________________________________

 
cur.execute('''DROP TABLE IF EXISTS pollution_2''')
cur.execute(""" CREATE TABLE IF NOT EXISTS pollution_2
( "departement_id_dept" INTEGER,
"commune_id_commune" INTEGER,
"stations_id_station" INTEGER,
"polluants_id" INTEGER,
"mesure_id_mesure" INTEGER,
"typologie" TEXT,
"influence" TEXT,
"id_poll_ue" INTEGER,
"date_debut" TIMESTAMP WITH TIME ZONE,
FOREIGN KEY ("departement_id_dept") REFERENCES departement ("id_dept"),
FOREIGN KEY ("commune_id_commune")  REFERENCES commune ("id_commune"),
FOREIGN KEY ("stations_id_station") REFERENCES stations ("id_station"),
FOREIGN KEY ("polluants_id") REFERENCES polluants ("id"));""")

 
cur.execute ("""delete from pollution_2 cascade""")

cur.execute("""INSERT INTO pollution_2 (departement_id_dept, commune_id_commune, stations_id_station, polluants_id, mesure_id_mesure, typologie, influence, id_poll_ue, date_debut)
select departement.id_dept, commune.id_commune, stations.id_station, polluants.id, Mesure.id_mesure, pollution.typologie, pollution.influence, pollution.id_poll_ue, pollution.date_debut
 
from pollution
 
JOIN departement
ON pollutIon.departement = departement.nom_dept
 
JOIN commune
ON pollution.commune = commune.nom_com
 
JOIN stations
ON pollution.station = stations.nom_station
 
JOIN polluants
ON pollution.polluant = polluants.nom_poll
 
join Mesure
on (stations.id_station, polluants.id, pollution.date_debut) = (Mesure.stations_id_station, Mesure.polluants_id, Mesure.date_debut);""")
 
#_______________________________________Impact du confinement sur la pollution_______________________________
 
#_____________________________________API des deux polluants (mensuel - année 2020)_________________________

covid_pm10 = requests.get('https://opendata.arcgis.com/datasets/a23d338f09d94c76ae5a1e3eac2b8ac6_4.geojson')
dict_pm10_covid = covid_pm10.json()
print(covid_pm10.status_code)
     
covid_no2 = requests.get('https://opendata.arcgis.com/datasets/a23d338f09d94c76ae5a1e3eac2b8ac6_1.geojson')
dict_no2_covid = covid_no2.json()
print(covid_no2.status_code)
     
list_polluant_covid = [dict_pm10_covid, dict_no2_covid]

print(len(list_polluant_covid))

#__________________________________création de la base de données avec les données brutes___________________________

db_dsn = "postgres://postgres:test@localhost:5432/decouverte"
db_args = parse_dsn(db_dsn)
conn = psycopg2.connect(**db_args)
     
cur = conn.cursor()
     
cur.execute('''DROP TABLE IF EXISTS pollution_covid''')
cur.execute('''CREATE TABLE IF NOT EXISTS pollution_covid("departement" TEXT, "commune" TEXT, "insee_com" INT, "station" TEXT, "code_station" TEXT, "typologie" TEXT, "influence" TEXT, "polluant" VARCHAR(32), "id_poll_ue" INT, "valeur" FLOAT, "unite" TEXT, "date_debut" TIMESTAMP WITH TIME ZONE, "date_fin" TIMESTAMP WITH TIME ZONE, "longitude" FLOAT, "lattitude" FLOAT)''')

for covid in list_polluant_covid:
    for elt in covid["features"]:
        confi = []
        for keys, values in elt["properties"].items():
            cov = ['nom_dept', 'nom_com', 'insee_com', 'nom_station', 'code_station', 'typologie', 'influence', 'nom_poll','id_poll_ue', 'valeur', 'unite', 'date_debut', 'date_fin', 'x_wgs84','y_wgs84']
            if keys in  cov:
                confi.append(values)
                print(keys, confi)
   
        print('\n')
        cur.execute("INSERT INTO pollution_covid(departement, commune, insee_com, station, code_station, typologie, influence, polluant, id_poll_ue, valeur, unite, date_debut, date_fin, longitude, lattitude) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", confi)

        
        
       
           
conn.commit()
cur.close()
conn.close()


#_______________________________________________Cartographie des stations___________________________________

ARA = [45.740858, 4.819629]

region = folium.Map(location = ARA, zoom_start = 7.5)


for element in dict_pm10["features"]:
    capteur = element["properties"]
    station = element['geometry']['coordinates']
    folium.Marker(location=[station[1],station[0]],popup = capteur["nom_station"]).add_to(region)

region
