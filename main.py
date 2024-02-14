from flask import Flask, render_template, jsonify
import os
import requests
from datetime import datetime
import json
import pymongo
import time
import schedule
from datetime import datetime
app = Flask(__name__)


@app.route('/')
def index():

      
      return render_template('index.html')


@app.route('/get_scores', methods=['GET'])
def get_scores():

          # Connexion à MongoDB
    uri = "mongodb+srv://usr:o54V5dcjJFisUGoo@mycluster.r0l4eum.mongodb.net/?retryWrites=true&w=majority"
    mongo = pymongo.MongoClient(uri, tls=True)
    db_scores = mongo.livescores.mycollection
    # Exclure l'objet _id lors de la récupération
    scores = db_scores.find_one({}, {'_id': False})
    if scores:
    # Convertir l'objet en une chaîne JSON
      scores_json_string = json.dumps(scores)
      return jsonify(scores_json_string)
    else:
      return 'No scores found in the database'
            
    url = 'https://api.football-data.org/v4/matches'
    headers = {'X-Auth-Token': '1b20f5f102d14320b82f892574c1bcbc'}
    response = requests.get(url, headers=headers)


    if response.status_code == 200:
        matches_data = response.json()
        return jsonify(matches_data)
    else:
        return jsonify({'error': 'Unable to fetch data'})
def sort_matches(match):
  # Définir l'ordre de priorité des statuts des matchs
  status_order = {'IN_PLAY': 3, 'PAUSED': 3, 'FINISHED': 1, 'SCHEDULED': 2, 'POSTPONED': 1, 'CANCELED': 1}

  # Extraire la date UTC du match
  utc_date = datetime.strptime(match['utcDate'], "%Y-%m-%dT%H:%M:%SZ")

  # Retourner un tuple contenant les critères de tri dans l'ordre de priorité
  return (status_order.get(match['status'], 0), utc_date, match['homeTeam']['name'], match['id'])
def push_scores():
  print('getting...')
  url = 'https://api.football-data.org/v4/matches'
  headers = {'X-Auth-Token': '1b20f5f102d14320b82f892574c1bcbc'}
  response = requests.get(url, headers=headers)
  print('success getting scores')
  print('pushing...')

  matches_data = response.json()

  # Ajoutez la date et l'heure actuelles à l'objet JSON
  now = datetime.now()
  matches_data["last-updated"] = now.strftime("%H:%M:%S")

  # Triez les matchs par leur ID
  matches_sorted = sorted(matches_data["matches"], key=sort_matches)
  uri = "mongodb+srv://usr:o54V5dcjJFisUGoo@mycluster.r0l4eum.mongodb.net/?retryWrites=true&w=majority"

  mongo = pymongo.MongoClient(uri, tls=True)

  db_scores = mongo.livescores.mycollection

  # Supprimez les documents existants dans la collection
  db_scores.delete_many({})

  # Insérez les matchs triés dans la base de données
  db_scores.insert_one({"Last-updated": matches_data["last-updated"], "matches": matches_sorted})

  print('finished')
  
schedule.every(10).seconds.do(push_scores) 

def execute_planified_tasks():
    while True:
        schedule.run_pending()
        time.sleep(1)

# Démarrer une thread pour exécuter les tâches planifiées en arrière-plan
import threading
task_thread = threading.Thread(target=execute_planified_tasks)
task_thread.start()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get("PORT"))

