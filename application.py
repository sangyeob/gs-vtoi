#-*- coding: utf-8 -*-

from boto.s3.connection import S3Connection
from boto.s3.key import Key
import os
import sqlite3
import time
import datetime
import hashlib
import md5
from flask import Flask, request, render_template, redirect, flash, url_for, g, session, abort, make_response, current_app, Response
from werkzeug import secure_filename
import sys
import json
import numpy
import imageio
from PIL import Image
from werkzeug.wsgi import LimitedStream
from datetime import timedelta
from functools import update_wrapper
import logging
import cStringIO
from flask.ext import restful
from flask.ext.restful import Api

#logging.basicConfig(filename='/opt/python/log/my.log', level=logging.DEBUG)

class StreamConsumingMiddleware(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        stream = LimitedStream(environ['wsgi.input'],
                               int(environ['CONTENT_LENGTH'] or 0))
        environ['wsgi.input'] = stream
        app_iter = self.app(environ, start_response)
        try:
            stream.exhaust()
            for event in app_iter:
                yield event
        finally:
            if hasattr(app_iter, 'close'):
                app_iter.close()
#s3 conn
conn = S3Connection(os.environ['AWS_ACCESS_KEY'], os.environ['AWS_SECRET_KEY'])
bucket = conn.get_bucket('gangnam-proto-image')

# configs
DATABASE = 'db/db.sqlite'
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'pw'

DEBUG = True

application = Flask(__name__)
application.config.from_object(__name__)

application.config['UPLOAD_FOLDER'] = 'static/uploads/'

api = restful.Api(application)

@application.route("/")
def index():
    return render_template('uploadpage.html', context = {})

@application.route("/upload/", methods=["POST", "OPTIONS"])
def upload():
    if request.files['0']:
        file = request.files['0']
        filename = hashlib.sha224(str(time.time())).hexdigest()
        cap = imageio.get_reader(file.read(), 'ffmpeg')
        size = cap.get_meta_data()['size']
        frames = cap.get_meta_data()['nframes']
        st = time.time()
        count = 0
        init = False
        err = False
        flip = 0
        if 'Android' in request.headers.get('User-Agent'):
            flip = 1
        else:
            flip = 2
        try:
            for i, image in enumerate(cap):
                if i >= count * frames / 50 - 0.01:
                    if flip == 1:
                        image = numpy.rot90(image)
                    elif flip == 2:
                        image = numpy.rot90(image, 3)
                    tmp = Image.fromarray(image)
                    if tmp.size[1] > tmp.size[0]:
                        tmp = tmp.resize((int(tmp.size[0] * (500.0 / tmp.size[0])), int(tmp.size[1] * (500.0 / tmp.size[0]))), Image.BILINEAR)
                        tmp = tmp.crop((0, tmp.size[1] / 2 - 250, 500, tmp.size[1] / 2 + 250))
                    else:
                        tmp = tmp.resize((int(tmp.size[0] * (500.0 / tmp.size[1])), int(tmp.size[1] * (500.0 / tmp.size[1]))), Image.BILINEAR)
                        tmp = tmp.crop((tmp.size[0] / 2 - 250, 0, tmp.size[0] / 2 + 250, 500))
                    image = numpy.array(tmp)
                    if i == 0:
                        board = image
                        thumb = Image.fromarray(image)
                        size = board.shape[:2]
                    else:
                        board = numpy.hstack((board, image))
                    count += 1
                if count >= 50:
                    break
        except:
            err = True
        im = Image.fromarray(board)
        elapsedTime = time.time() - st
        filename = filename + '.png'
        memoryFile = cStringIO.StringIO()
        im.save(memoryFile, 'png')
        k = Key(bucket)
        k.key = filename
        k.set_contents_from_string(memoryFile.getvalue())
        k.set_acl('public-read')
        memoryFile.close()
        memoryFile = cStringIO.StringIO()
        thumb.save(memoryFile, 'png')
        k = Key(bucket)
        k.key = filename + 'thumbnail'
        k.set_contents_from_string(memoryFile.getvalue())
        k.set_acl('public-read')
        memoryFile.close()
        return json.dumps({
                'url': 'https://s3-ap-northeast-1.amazonaws.com/gangnam-proto-image/' + filename,
                'thumbnail': 'https://s3-ap-northeast-1.amazonaws.com/gangnam-proto-image/' + filename + 'thumbnail',
                'frames': count,
                'size': size
            })
    else:
        return "Failed"

@application.route("/view/<filename>/")
def view(filename):
    return render_template('imageslidersample.html', context = { 'url': filename})

@application.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'ORIGIN, X-REQUESTED-WITH, CONTENT-TYPE, ACCEPT, X-PINGOTHER')
    response.headers.add('Access-Control-Allow-Methods', 'GET, PUT, OPTIONS, POST, DELETE')
    return response

if __name__ == "__main__":
    application.wsgi_app = StreamConsumingMiddleware(application.wsgi_app)
    reload(sys)
    sys.setdefaultencoding('utf-8')
    application.debug = True
    application.run(host='0.0.0.0', port=4000, threaded=True)