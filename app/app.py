
from flask import Flask, render_template, request
import json

import psycopg2

from Recommendations import Recommendation

app = Flask(__name__)

img_data = [
    {"title": "Movie: 25198.jpg", "imgpath": "images/sample/25198.jpg"}, 
    {"title": "Movie: 25239.jpg", "imgpath": "images/sample/25239.jpg"}, 
    {"title": "Movie: 25211.jpg", "imgpath": "images/sample/25211.jpg"}, 
    {"title": "Movie: 25238.jpg", "imgpath": "images/sample/25238.jpg"}, 
    {"title": "Movie: 25202.jpg", "imgpath": "images/sample/25202.jpg"}, 
    {"title": "Movie: 25189.jpg", "imgpath": "images/sample/25189.jpg"}, 
    {"title": "Movie: 25214.jpg", "imgpath": "images/sample/25214.jpg"}, 
    {"title": "Movie: 25228.jpg", "imgpath": "images/sample/25228.jpg"}, 
    {"title": "Movie: 25272.jpg", "imgpath": "images/sample/25272.jpg"}, 
    {"title": "Movie: 25263.jpg", "imgpath": "images/sample/25263.jpg"}, 
    {"title": "Movie: 25251.jpg", "imgpath": "images/sample/25251.jpg"}, 
    {"title": "Movie: 25227.jpg", "imgpath": "images/sample/25227.jpg"}
    ]

@app.route('/')
def index():
    r = Recommendation()
    
    return render_template("index.html",cards=img_data)

@app.route("/search")
def search():
    return render_template("search.html")

@app.route("/account")
def account():
    return "Oops, you caught me! I didn't make the account page yet..."

@app.route("/about")
def about():
    return "Oops, you caught me! I didn't make the about page yet..."






if __name__ == "__main__":
    app.run(debug=True)
