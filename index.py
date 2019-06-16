#!/usr/bin/env python
from flask import Flask, render_template, request, send_file

from six import *
import json

app = Flask(__name__)
#url_for('static', filename='style.css')

tmp_dir = '/ramdisk/'
detection_json = 'detection.json'
image_file = 'capture.jpg'
default = {"active" : True, "visualisation" : False}


def read_file(jsonfile_name):
    try:
        app.logger.debug("Read json file....")
        with open(jsonfile_name, 'r') as jsonfile:
            datas = json.load(jsonfile)
            app.logger.debug("ok")
    except Exception:
        app.logger.debug("No datas!")
        datas = {}
    return datas

def write_file(datas, jsonfile_name):
    try:
        app.logger.debug("Write json file....")
        with open(jsonfile_name, 'w') as jsonfile:
            print(datas)
            json.dump(datas, jsonfile)
            app.logger.debug("ok")
    except Exception as e:
        app.logger.debug("Error during write json file : %s"%e)

@app.route('/')
def index():
    datas = dict(default)
    datas.update(read_file(tmp_dir+detection_json))
    write_file(datas, tmp_dir+detection_json)
    if datas['visualisation']:
        image = '/' + image_file
    else:
        image = ""
    return render_template('index.html', datas = datas,  image = image)

@app.route('/<command>/<action>')
def cmd(command, action):
    print("Cmd : %s,%s"%(command, action))
    datas = dict(default)
    datas.update(read_file(tmp_dir+detection_json))
    if command == "camera":
        datas["active"]=action == "on"
    if command == "visualisation":
        datas["visualisation"]=action == "on"
    write_file(datas, tmp_dir+detection_json)
    if datas['visualisation']:
        image = '/' + image_file
    else:
        image = ""
    return render_template('index.html', datas = datas,  image = image)

@app.route('/json')
def show_json():
    datas = dict(default)
    datas.update(read_file(tmp_dir+detection_json))
    return json.dumps(datas)

@app.route('/'+image_file)
def send_image_file():
    print("Send %s"%tmp_dir+image_file)
    return send_file(tmp_dir+image_file, mimetype='image/gif')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
