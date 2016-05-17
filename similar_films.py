#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-05-14 21:29:10
# @Author  : Carlo (carlo.villamayor@gmail.com)
# @Link    : https://github.com/volrac/similar_films
# @Version : 0.1

import os
import sys
import requests
import bs4
import re
import urllib
import datetime
import pandas as pd
from re import sub

def get_soup(url):
	"""
	gets BeautifulSoup object of downloaded url
	"""

	# add fake headers to avoid being detected as a bot
	headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
	r = requests.get(url, headers=headers)
	html = r.content
	soup = bs4.BeautifulSoup(html,'html.parser')

	return soup

def is_movie_link(href):
	match = re.search(r'^/movies/\?id=.*',href)

	return match

def find_box_office_mojo_link(args):
	"""
	Find top match in Box Office Mojo for given Movie Title
	"""
	base_url = 'http://www.boxofficemojo.com'

	title = " ".join(args)
	title = urllib.quote(title)
	url = base_url + '/search/?q=' + title + '&sort=gross';

	soup = get_soup(url)

	match_url = False

	tables = soup.find_all('table')

	for table in tables:
		match = re.search(r'Movie\sTitle\s\(click\stitle\sto\sview\)',table.get_text())

		if match:
			rows = table.find_all('tr')
			if len(rows) > 1:
				for row in rows:
					tds = row.find_all('td')
					if len(tds) > 0:

						link = tds[0].find('a')
						if link > 0:
							href = link['href']
							match = is_movie_link(href)

							if match:
								try:
									release_date = datetime.datetime.strptime(tds[6].get_text(),"%m/%d/%Y")
									if release_date <= datetime.datetime.now():
										match_url = base_url + href
										break
								except:
									continue
	if not match_url:
		return False

	return match_url

def find_rotten_tomatoes_rating(title):
	"""
	Get Rotten Tomatoes rating for given Movie Title
	"""
	title = urllib.quote(title)
	url = 'http://www.rottentomatoes.com/search/?search=' + title
	soup = get_soup(url)
	
	rating = 0

	movies = soup.find('ul',{'id':'movie_results_ul'})
	if movies:
		movie_titles = movies.find_all('a',{'class':'articleLink','title': None})

		rating_key = 0
		for key, movie_title in enumerate(movie_titles):
			if movie_title.get_text().lower().strip() == urllib.unquote_plus(title.lower()).strip():
				rating_key = key
				break

		scores = soup.find_all('span',{'class':'tMeterScore'})
		if len(scores) > rating_key:
			score = scores[rating_key]
			rating = score.get_text()
			rating = rating.replace("%","")

	return int(rating)

def find_metacritic_rating(title):
	"""
	Get Metacritic rating for given Movie Title
	"""

	title = urllib.quote(title)
	url = 'http://www.metacritic.com/search/movie/' + title + '/results'
	soup = get_soup(url)
	
	rating = 0
	score = soup.find('span',{'class':'metascore_w'})
	if score:
		rating = score.get_text()

	return int(rating)

def remove_year_from_title(movie_title):
	"""
	Removes appended year from title
	"""
	match = re.search(r'(.+)(\s\(\d\d\d\d\))',movie_title)
	if match:
		movie_title = match.group(1)

	return movie_title

def get_boxofficemojo_title(boxofficemojo_url):
	"""
	Parse Movie Title from Box Office Mojo Url
	"""
	movie_title = ''

	soup = get_soup(boxofficemojo_url)
	if soup.title:
		# get movie title from page
		movie_title = soup.title.get_text().replace(" - Similar Movies - Box Office Mojo","")
		movie_title = remove_year_from_title(movie_title)

	return movie_title

def find_similar_movies(boxofficemojo_url):
	"""
	Find Similar Movies to given Partial Movie Title
	"""
	movie_dict_list = []

	similar_url = boxofficemojo_url + '&page=similar'

	soup = get_soup(similar_url)

	# get table that lists similar movies
	similar_table = soup.find('table',{'class':'chart-wide'})
	
	if similar_table:
		# get rows in similars table
		rows = similar_table.find_all('tr')
		if len(rows) > 0:
			for row in rows:
				# get each column in each row
				tds = row.find_all('td')

				if len(tds) > 0:

					link = tds[0].find('a')
					if link:
						href = link['href']
						match = is_movie_link(href)

						if match:

							# Movie Title
							title = link.get_text()
							title = remove_year_from_title(title)

							# Gross Receipts
							gross = tds[2].get_text()
							try:
								gross = float(sub(r'[^\d.]', '', gross))
							except ValueError:
								gross = 0

							# Number of Theaters shown in
							theaters = tds[3].get_text()
							try:
								theaters = int(sub(r'[^\d.]', '', theaters))
							except ValueError:
								theaters = 0

							# Gross Per Theater
							try:
								per_theater = gross / theaters
							except ZeroDivisionError:
								per_theater = 0

							# Rotten Tomatoes rating
							rotten_tomatoes = find_rotten_tomatoes_rating(title)

							# Meta Critic Rating
							metacritic = find_metacritic_rating(title)

							# Custom Sorting Algorithm
							custom_value = (rotten_tomatoes + metacritic) / 2  * per_theater

							movie_dict = {
								'title': title,
								'gross': gross,
								'theaters': theaters,
								'per_theater': per_theater,
								'rotten_tomatoes': rotten_tomatoes,
								'metacritic': metacritic,
								'custom_value': custom_value,
							}

							movie_dict_list.append(movie_dict)

	return movie_dict_list


def main():
	
	args = sys.argv[1:]

	if not args:
		print 'usage: [--sotby column] movie title'
		sys.exit(1)
	
	sortby = 'custom_value'
	if args[0] == '--sortby':
		sortby = args[1]
		del args[0:2]

	title = " ".join(args)
	print 'Searching for movies with titles matching "' + title + '"'

	boxofficemojo_url = find_box_office_mojo_link(args)
	if(boxofficemojo_url == False):
		print "No movie with title found."
		sys.exit(1)

	print 'Top Match Found: ' + get_boxofficemojo_title(boxofficemojo_url)

	similar_movies = find_similar_movies(boxofficemojo_url)

	if len(similar_movies) > 0:
		print 'Printing results sorted by ' + sortby
		df = pd.DataFrame(similar_movies)
		df = df.sort_values(by=sortby, ascending=False)

		print df
	else:
		print 'No similar movies found.'

	return True

if __name__ == '__main__':
	main()