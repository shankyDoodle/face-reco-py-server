from flask import Flask, render_template, request, send_file, redirect, url_for,flash,send_from_directory, jsonify
import sqlite3
import io
import os
from werkzeug.utils import secure_filename
import base64


import cred
creds = cred.wharAreMyCreds()
import boto3
client = boto3.client('rekognition',
                      aws_access_key_id=creds[0],
                      aws_secret_access_key=creds[1],
                      region_name='us-east-1')

UPLOAD_FOLDER = '/Users/shankydoodle/Assignments/2Spring2019/Game/Project_7_8/face-reko-py-server/uploads'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 * 1024 * 1024 * 1024

app.secret_key = 'super secret key'
# app.config['SESSION_TYPE'] = 'filesystem'

def createDBTable():
    conn = sqlite3.connect('imagestorage.db')
    c = conn.cursor()
    conn.execute('''DROP TABLE IF EXISTS referencedimages''')
    c.execute('''CREATE TABLE referencedimages (name text, imagedata text)''')

    conn.execute('''DROP TABLE IF EXISTS recoimages''')
    c.execute('''CREATE TABLE recoimages (name text, imagedata text)''')
    conn.close()


@app.route('/')
def hello_world():
    # createDBTable()
    return render_template('index.html')
    # return "Hello World"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploadtraining', methods=['POST'])
def upload_file():
    returned = request.files['file']
    bytesarray = returned.read()

    try:
        conn = sqlite3.connect('imagestorage.db')
        c = conn.cursor()
        c.execute('insert into referencedimages values (?,?)', [returned.filename, sqlite3.Binary(bytesarray)])

        # file2 = c.execute('select imagedata from referencedimages where name=?', (returned.filename,)).fetchone()[0]
        conn.commit()
        conn.close()

        # file3 = io.BytesIO(file2)
        # return send_file(file3, attachment_filename='logo.png', mimetype='image/png')
        return "File Upload Success!!!"
    except Exception as e:
        print(e)
        return "Failed Upload failed" + str(e)

@app.route('/uploadrecognize', methods=['POST'])
def recognize_file():
    try:
        returned = request.files['file2']
        target_image = returned.read()

        conn = sqlite3.connect('imagestorage.db')
        c = conn.cursor()
        sourcefiles = c.execute('select * from referencedimages',).fetchall()

        c.execute('insert into recoimages values (?,?)', [returned.filename, sqlite3.Binary(target_image)])

        conn.commit()
        conn.close()

        faces_matched = []
        faces_unmatched = []
        for fileindex in range(len(sourcefiles)):
            fh = open("./uploads/imageToSave.png", "wb")
            fh.write(sourcefiles[fileindex][1])
            fh.close()

            source_image = open('./uploads/imageToSave.png', 'rb')

            response = client.compare_faces(
                SourceImage={
                    'Bytes': source_image.read(),
                },
                TargetImage={
                    'Bytes': target_image,
                }
            )

            if len(response["FaceMatches"]) > 0 and response["FaceMatches"][0]["Similarity"] > 80:
                faces_matched.append(sourcefiles[fileindex][0])
            else:
                faces_unmatched.append(sourcefiles[fileindex][0])

        return jsonify(mathedFaces=faces_matched, unmatchedFaces=faces_unmatched)
    except Exception as e:
        print(e)
        return "Failed Upload failed" + str(e)

if __name__ == '__main__':
    app.run(host='0.0.0.0')

# lt --port 5000