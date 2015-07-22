from flask import Flask, render_template, request
from application import db
from application.models import Data
from application.forms import EnterDBInfo
import json
import requests
import pickle
import numpy as np 
import MySQLdb as mdb
import scipy
from scipy.spatial.distance import cosine as cosim

# Functions:
# Fetch index for given entry of list
def getIndex(element, my_list):
    # Create a generator
    gen = (i for i,x in enumerate(my_list) if x == element)
    for i in gen:
        return i

# Order-1 normalization (a1+a2+...=1)
def norm1(v):
    scaled_vector = []
    total_A = float(sum(v))
    if total_A == 0:
        return None
    for i in v:
        scaled_vector.append(i/total_A)
    return scaled_vector

def getArtists(venue_id):
    token = 'WGLTwENb36bAgHNc'
    query_params = { 'apikey': token,
                     'per_page': 50,
                     'page': 1}
    endpoint = 'http://api.songkick.com/api/3.0/venues/' + str(venue_id) + '/calendar.json?'

    response = requests.get(endpoint, params=query_params)
    total_results = response.json()['resultsPage']['totalEntries']
    if total_results == 0:
        return []
    
    full_data = response.json()['resultsPage']['results']['event']
    if not full_data:
        return []
    
    ev_date = full_data[0]['start']['date']
    ev_name = full_data[0]['displayName']
    ev_artists = []
    # 0 means first event, could change it to future events
    for artist in full_data[0]['performance']:
        ev_artists.append(artist['artist']['displayName'])
        #print artist['artist']['displayName'], artist['artist']['id']

    return [ev_name, ev_date, ev_artists]

token = 'WL4JBSOI4ZGXPY8FN'

#raw_string = "Radiohead, miles davis"
#artists = raw_string.split(",")

query_params = { 'api_key': token,
                 'name': "",
                 'bucket': 'familiarity',
                 'bucket': 'terms'}

endpoint = 'http://developer.echonest.com/api/v4/artist/profile?'

# Elastic Beanstalk initalization
application = Flask(__name__)
application.debug=True
# change this to your own value
application.secret_key = 'cC1YCIWOj9GgWspgNEo2'   

@application.route('/', methods=['GET', 'POST'])
@application.route('/<city>', methods=['GET', 'POST'])
def index(city='SF'):

    form1 = EnterDBInfo(request.form, fld2=city)
    # Remains empty on first page load    
    if request.method == 'POST' and form1.validate():

        regional_good_venues = pickle.load( open( city+"/regional_good_venues.pickle", "rb" ) )
        master_genre_map = pickle.load( open( city+"/master_genre_map.pickle", "rb" ) )
        master_genre_idf = pickle.load( open( city+"/master_genre_idf.pickle", "rb" ) )
        master_venue_vect = pickle.load( open( city+"/master_venue_vect.pickle", "rb" ) )
        master_venue_list = pickle.load( open( city+"/master_venue_list.pickle", "rb" ) )
        venue_ids = pickle.load( open( city+"/venue_ids.pickle", "rb" ) )
        venue_list = pickle.load( open( city+"/venue_list.pickle", "rb" ) )
        locations = pickle.load( open( city+"/locations.pickle", "rb" ) )
        k_means = pickle.load( open( city+"/k_means.pickle", "rb" ) )
        region_artists = pickle.load( open( city+"/regional_subset.pickle", "rb" ) )


        def getEvtVector(artist_names):
            ev_vector = np.array([0.] * len(master_genre_idf))
            for artist in artist_names:
                if artist in region_artists:
                    ev_vector += region_artists[artist]
            return ev_vector



        # One pack per artist
        raw_string = form1.dbNotes.data
        artists = raw_string.split(",")
        venue_pack = []
        pretty_artist_names = []
        for artist in artists: #artists.split(","):
    
            query_params['name'] = artist.lstrip().rstrip()
    
            response = requests.get(endpoint, params=query_params)
            full_data = response.json()

            if response.json()['response']['status']['message'] != 'Success':
                continue
        
            terms = full_data['response']['artist']['terms']
            pretty_artist_names.append(full_data['response']['artist']['name'])
            genre_vec = [0] * len(master_genre_map)
            # Loop over genres, make vector of frequencies
            for term in terms:
                # Get index of genre in master_genre_map
                indx = getIndex(term['name'], master_genre_map)
                if indx is None:
                    continue
                # Set corresponding vector entry to value of frequency
                genre_vec[indx] = term['frequency']
            if norm1(genre_vec) is None:
                continue
            # Set key to artist name, value is array of (normalized) freqs
            scaled_vec = np.array(norm1(genre_vec))
            # Apply tf-idf
            tfidf = scaled_vec*master_genre_idf
            # Last step, normalize vector:
            user_artist_vec = tfidf/np.linalg.norm(tfidf)
            p_index = k_means.predict(user_artist_vec)
 
            #con = mdb.connect('localhost', 'root', '', 'scenehash');
            #cur = con.cursor()
            #cur.execute("SELECT artist_id, artist FROM events")
            #rows = cur.fetchall()
            #for row in rows:
            #    print row

            venues = []
            best_score = 1.0
            for i in range(len(master_venue_list)):
                if k_means.labels_[i] == p_index[0]:
                    target_venue = dict()
                    ind = getIndex(master_venue_list[i], venue_list)
                    evt_details = getArtists(venue_ids[ind] )
                    if len(evt_details) == 0:
                        continue
                    # Find score, check if best
                    target_venue['score'] = cosim(user_artist_vec, getEvtVector(evt_details[2]))
                    #if score < best_score:
                    if np.isnan(target_venue['score']):
                        #target_venue['score'] = 1.01 #At least scores of 1.00 exist!
                        continue
                    target_venue['ven_name'] = master_venue_list[i]
                    target_venue['lat'] = locations[ind][0]
                    target_venue['lon'] = locations[ind][1]
                    target_venue['vid'] = venue_ids[ind]
                    target_venue['url'] = 'http://eventful.com/'
                    target_venue['evt_name'] = evt_details[0]
                    target_venue['evt_date'] = evt_details[1]
                    venues.append(target_venue)

            # Sort by score
            sorted_by_score = sorted(venues, key=lambda k: k['score']) 
            venue_pack.append(sorted_by_score)

        if not venue_pack:
            return render_template('index.html', form1=form1, city_region=city, message="No artists matched!", coords=json.dumps(venue_pack))

        return render_template('index.html', form1=form1, city_region=city, message="", 
                               user_artist_list=json.dumps(pretty_artist_names), 
                               coords=json.dumps(venue_pack))


        
    return render_template('index.html', form1=form1, message="", city_region=city, coords=json.dumps([]))

@application.route('/slides', methods=['GET'])
def slides():
    return render_template('slides.html')

@application.route('/blog', methods=['GET'])
def blog():
    return render_template('blog.html')


if __name__ == '__main__':
    application.run(host='0.0.0.0', port=80)
