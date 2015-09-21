# SceneHash
Web app for finding live shows and venues based on your favorite artists.

[Scene Hash](http://scenehash.com)

### Description:
Created during the Insight Data Science Fellows Program, SceneHash is a web application for finding local music events. I developed a “music2vec” model to facilitate comparisons among genres, artists, and venues, and employed k-means clustering algorithm with scikit-learn. Combined Flask, Leaflet.js, and jQuery to create interactive an web application deployed on AWS.

To do: add functionality to input a genre instead of artist.

### Directory Structure
**venv/** Virtual environment

**index/** Flask application. 

**analysis/** Analysis code in the form of IPython notebooks, outlined as follows:
- 1_pullVenByCity.ipynb (Fetch all available venues in a metro region, store in MYSQL database.)
- 2_pullEvtByVenue.ipynb (Fetch all upcoming events at venues, by city/metro region.)
- 3_artist_pipeline.ipynb (Vectorize, perform tf-idf transformation, create vectors for venues.)
- 4_clustering.ipynb	(Perform clustering, save trained model as pickle output for website.)
- 5_predict.ipynb	(Development code, used to vectorize upcoming events and sort by cosine similarity. Final version of this code ended up in Flask application online.)
- 6_validation.ipynb (Artists randomly removed before clustering, check how often corresponding venue is recalled in "best" cluster.)
