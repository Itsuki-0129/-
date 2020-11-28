from flask import Flask, render_template, request, json, jsonify
import pymysql
import requests
app = Flask(__name__)

@app.route('/', methods = ["GET", "POST"])
def index():
    return render_template("index.html")

@app.route('/login', methods = ["GET", "POST"])
def login_form():
    return render_template("login.html")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)