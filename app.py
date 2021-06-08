from enum import unique
from flask import Flask, render_template, request, json, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import urllib.request
from urllib.request import Request,urlopen
import sqlite3
import csv
import pandas as pd


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_BINDS'] = {'movies': 'sqlite:///movies.db'}
db = SQLAlchemy(app)

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)

    def __repr__(self) -> str:
        return f"{self.id} - {self.username}"

class Movies(db.Model):
    __bind_key__ = 'movies'
    index = db.Column(db.Integer, primary_key=True)
    userid = db.Column(db.Integer, nullable = False)
    itemid = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    imdbrating = db.Column(db.Float, nullable=False)
    title =  db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"{self.userid} - {self.rating}"


@app.route("/", methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        mk = request.form['mk']
        mk = mk.replace(" ","+")
        url = 'http://www.omdbapi.com/?apikey=b13aa98f&s='
        url = url + str(mk)
        json_obj = urllib.request.urlopen(url)
        data = json.load(json_obj)
        data = data['Search']
        print(data)
        return render_template('about.html',data=data)
    
    return render_template('homepage.html')

@app.route("/home", methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route("/signup", methods=['GET', 'POST'])
def signup():
    return render_template('signup.html')

@app.route("/login", methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route("/success", methods=['GET', 'POST'])
def success():
    return render_template('success.html')

@app.route("/recommendation", methods=['GET', 'POST'])
def recommendation():
    column_names = ['user_id', 'item_id', 'rating', 'timestamp']
    path = 'D:\Sem4\SE\Project_implementation\\file.tsv'
    movie_titles = pd.read_csv('D:\Sem4\SE\Project_implementation\Movie_Id_Titles.csv')
    df = pd.read_csv(path, sep='\t', names=column_names)
    data = pd.merge(df, movie_titles, on='item_id')

    ratings = pd.DataFrame(data.groupby('title')['rating'].mean()) 
    ratings['num of ratings'] = pd.DataFrame(data.groupby('title')['rating'].count())

    moviemat = data.pivot_table(index ='user_id',columns ='title', values ='rating')

    search_data = pd.read_csv('D:\Sem4\SE\Project_implementation\movies.csv')
    search_data['netrating'] = (search_data['rating']*3 + search_data['imdbrating'])/5
    req_data = search_data[search_data['userid']==myUser[0][0]]
    req_data = req_data.sort_values(by = 'netrating', ascending = False)
    req_data = req_data.reset_index(drop = True)
    user_ratings = moviemat[str(req_data.at[0,'title']) + " (" + str(req_data.at[0,'year']) + ")"]
    
    similar_to = moviemat.corrwith(user_ratings)
    corr = pd.DataFrame(similar_to, columns =['Correlation'])
    corr.dropna(inplace = True)

    corr = corr.sort_values('Correlation', ascending = False)
    corr = corr.join(ratings['num of ratings'])

    corr = corr[corr['num of ratings']>100].sort_values('Correlation', ascending = False)
    prediction = corr.index
    url ='http://www.omdbapi.com/?apikey=b13aa98f&t='
    data = []

    for i in range(1,5):
        part_i = prediction[i].rpartition(' (')
        part_i =part_i[0].replace(' ','+')
        print(part_i)
        json_obj=urllib.request.urlopen(url+str(part_i))
        rec_data=json.load(json_obj)
        data.append(rec_data)
    
    print(data)
        
    return render_template('recommendation.html',data=data)


@app.route("/rating", methods=['GET', 'POST'])
def rating():
    with sqlite3.connect("movies.db") as conn:
        cursor=conn.cursor()
        rate = request.form.get('stars')

        cursor.execute(" INSERT INTO `movies` (`index`,`userid`,`itemid`,`rating`,`imdbrating`,`title`,`year`,`timestamp`) VALUES (NULL,'{}','{}','{}','{}','{}','{}','{}')"
        .format(myUser[0][0],itemid,rate,imdbrate,title,relyear,datetime.utcnow()))

        cursor.execute("select * from `movies`;")
        with open("movies.csv", "w", newline='') as csv_file:  # Python 3 version    
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow([i[0] for i in cursor.description])
            csv_writer.writerows(cursor)
    
    return render_template('info.html', data = info)

@app.route("/add_user", methods=['POST'])
def add_user():
    with sqlite3.connect("users.db") as conn:
        cursor=conn.cursor()
        name = request.form.get('uname')
        email = request.form.get('uemail')
        password = request.form.get('upassword')

        cursor.execute(" INSERT INTO `users` (`id`,`username`,`email`,`password`) VALUES (NULL,'{}','{}','{}')"
        .format(name,email,password))

        conn.commit()
        
    return redirect('/success')

@app.route("/login_validation", methods=['POST'])
def login_validation():
    with sqlite3.connect("users.db") as conn:
        cursor=conn.cursor()
        email = request.form.get('email')
        password = request.form.get('password')
        cursor.execute(" SELECT * FROM `users` WHERE `email` LIKE '{}' AND `password` LIKE '{}' "
        .format(email,password))
        global myUser 
        myUser= cursor.fetchall()
        if len(myUser)>0:
            return redirect('/home') 
        else:
            return redirect('/login')

@app.route("/about",methods=['GET','POST']) 
def about():
    if request.method=='POST': 
        imdb_id=request.form['imdbid']
        link='http://www.omdbapi.com/?apikey=b13aa98f&i='+str(imdb_id) 
        obj=urllib.request.urlopen(link)
        global itemid,info,title,imdbrate,relyear
        info=json.load(obj)
        itemid = info['imdbID']
        title = info['Title']
        imdbrate = info['imdbRating']
        relyear = info['Year']
        return render_template('info.html',data=info)

if __name__== "__main__":
    app.run(debug=True)
 