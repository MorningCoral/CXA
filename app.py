from flask import Flask, render_template, request, session
import os
import urllib
from bs4 import BeautifulSoup
import requests
import sys
sys.path.insert(0,'static/videos/')
from demo import predict

app = Flask(__name__)
app.secret_key = 'hi'

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def index():
	session['stage'] = 0
	session['prediction1'] = "waiting"
	session['prediction2'] = "waiting"
	session['prediction3'] = "waiting"
	return render_template("index.html")


@app.route('/surveillance', methods=['POST','GET'])
def surveillance():
	station = "None"
	cam1 = "../static/images/Camnormal.png"
	cam2 = "../static/images/Camnormal.png"
	cam3 = "../static/images/Camnormal.png"
	if session['stage'] == 0:
		target = os.path.join(APP_ROOT, 'static/videos')
		print(target)

		if not os.path.isdir(target):
			os.mkdir(target)

		session['filenames'] = []
		for file in request.files.getlist("file"):
			print(file)
			session['filenames'].append(file.filename)
			destination = "/".join([target, file.filename])
			print(destination)
			file.save(destination)

		text = urllib.parse.quote_plus("where is the nearest police station")
		url = 'https://google.com/search?q=' + text
		response = requests.get(url)
		soup = BeautifulSoup(response.text,'lxml')
		for g in soup.find_all(class_='kR1eme rllt__wrap-on-expand'):
			station = g.span.text
			break

	# model can be one of lstm, lrcn, mlp, conv_3d, c3d.
	model = 'lrcn'
	# Must be a weights file.
	saved_model = 'static/videos/lrcn-images.114-2.304.hdf5'
	# Sequence length must match the lengh used during training.
	seq_length = 40
	# Limit must match that used during training.
	class_limit = None

	if model in ['conv_3d', 'c3d', 'lrcn']:
		data_type = 'images'
		image_shape = (80, 80, 3)
	elif model in ['lstm', 'mlp']:
		data_type = 'features'
		image_shape = None
	else:
		raise ValueError("Invalid model. See train.py for options.")

	if session['stage'] <3:
		prediction = predict(data_type, seq_length, saved_model, image_shape, os.path.splitext(session['filenames'][session['stage']])[0], class_limit)
		session['stage'] += 1
		if session['stage'] == 1:
			session['prediction1'] = prediction
		if session['stage'] == 2:
			session['prediction2'] = prediction
		if session['stage'] == 3:
			session['prediction3'] = prediction

		if "Crime Detected" in prediction:
			if session['stage'] == 1:
				cam1 = "../static/images/camalert.gif"
			if session['stage'] == 2:
				cam2 = "../static/images/camalert.gif"
			if session['stage'] == 3:
				cam3 = "../static/images/camalert.gif"


	return render_template("surveillance.html", video0="../static/videos/" + session['filenames'][0], 
		video1="../static/videos/" + session['filenames'][1], video2="../static/videos/" + session['filenames'][2], 
		station=station, prediction1=session['prediction1'], prediction2=session['prediction2'], 
		prediction3=session['prediction3'], stage = session['stage'], cam1=cam1, cam2=cam2, cam3=cam3)

if __name__ == "__main__":
	app.run(port="5000", debug=True)