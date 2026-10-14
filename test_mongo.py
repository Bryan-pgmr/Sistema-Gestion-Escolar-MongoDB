from pymongo import MongoClient

# Configura la conexión con tus datos
usuario = "admin"
password = "admin12345"
basedatos = "bigdata2"
coleccion = "alumnos"

uri = f"mongodb://{usuario}:{password}@localhost:27017/{basedatos}?authSource=admin"
client = MongoClient(uri)

db = client[basedatos]
col = db[coleccion]

# Imprime los documentos de la colección
for doc in col.find():
    print(doc)

