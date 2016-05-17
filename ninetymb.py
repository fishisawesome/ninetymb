from flask import Flask
from flask import request
from flask import abort, redirect, url_for
from flask import render_template

import urllib
import similar_films as sf

app = Flask(__name__)

@app.route('/')
def hello_world():
	if request.args.get('title'):
		return redirect( url_for('search', title=request.args.get('title') ) )
	else:
		return render_template('index.html')


@app.route('/search')
@app.route('/search/<title>')
def search(title = None):
	
	if request.args.get('sort'):
		sortby = request.args.get('sort')
	else:
		sortby = 'custom_value'

	if title == None:
		return 'Please provide a title'

	title = title.split(" ")

	boxofficemojo_url = sf.find_box_office_mojo_link(title)

	movie_title = sf.get_boxofficemojo_title(boxofficemojo_url)

	if(movie_title == False):
		return 'Movie not found'

	similar_movies = sf.find_similar_movies(boxofficemojo_url)

	if len(similar_movies) > 0:
		return render_template('search.html',
								movie_title= movie_title,
								similar_movies = similar_movies
								)
	else:
		return 'No similar movies found.'

if __name__ == '__main__':
	app.debug = True
	app.run()