#This is the main file where I have integrated html files with flask framework
#Importing all the neccessary modules and libraries

from flask import Flask, flash, redirect, render_template, request, session
from cs50 import SQL
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
# Importing library that recognizes face in my application  
import face_recognition

import zlib
from functools import wraps
from base64 import  b64decode




# Configuring the application
app = Flask(__name__)
#configure flask-socketio 

# Ensuring templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensuring responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response



# Configuring session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configuring CS50 Library to use SQLite database
db = SQL("sqlite:///records.db")


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


#By default login page would appear
@app.route("/")
@login_required


#Defining login page as home page
def home():
    return redirect("/home")
@app.route("/home")
@login_required


def index():
    return render_template("index.html")


#Function that Logs user in
@app.route("/login", methods=["GET", "POST"])
def login():
    

    # Forget any user_id of previous sessions
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Assign inputs to variables
        input_username = request.form.get("username")
        input_password = request.form.get("password")

        # Ensure username was submitted else display message
        if not input_username:
            return render_template("login.html",messager = 1)



        # Ensure password was submitted else display message
        elif not input_password:
             return render_template("login.html",messager = 2)

        # Query database for username using sqlite
        username = db.execute("SELECT * FROM users WHERE username = :username",
                              username=input_username)

        # Ensure username exists and password is correct else display message
        if len(username) != 1 or not check_password_hash(username[0]["hash"], input_password):
            return render_template("login.html",messager = 3)

        # Remember which user has logged in until he/she logs out
        session["user_id"] = username[0]["id"]



        # Everything is correct hence display that you've loged in
        return render_template("index.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


# Function via which user logs out
@app.route("/logout")
def logout():
    
    # Forget any user_id of any previous sessions
    session.clear()

    # Redirect user to login form
    return redirect("/")


#Function via which new user registers
@app.route("/register", methods=["GET", "POST"])
def register():
    
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Assign inputs to variables
        input_username = request.form.get("username")
        input_password = request.form.get("password")
        input_confirmation = request.form.get("confirmation")

        # Ensure username was submitted else display message
        if not input_username:
            return render_template("register.html",messager = 1)

        # Ensure password was submitted else display message
        elif not input_password:
            return render_template("register.html",messager = 2)

        # Ensure passwsord confirmation was submitted else display message
        elif not input_confirmation:
            return render_template("register.html",messager = 4)

        #If imput password and confirmation password doesn't match display a message
        elif not input_password == input_confirmation:
            return render_template("register.html",messager = 3)

        # Query database for username using sqlite
        username = db.execute("SELECT username FROM users WHERE username = :username",
                              username=input_username)

        # Ensure username is not already taken else display message
        if len(username) == 1:
            return render_template("register.html",messager = 5)

        # Query database to insert new user
        else:
            new_user = db.execute("INSERT INTO users (username, hash) VALUES (:username, :password)",
                                  username=input_username,
                                  password=generate_password_hash(input_password, method="pbkdf2:sha256", salt_length=8))

            if new_user:
                # Keep newly registered user logged in
                session["user_id"] = new_user

           

            # As user has registered username and password ask him to get his image registered for face recognisation
            return render_template("setup.html")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



#When user choses to unlock using face password
@app.route("/facereg", methods=["GET", "POST"])
def facereg():
    # Forget any user_id of any previous sessions
    session.clear()
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #get the image we got from the webcam encoded
        encoded_image = (request.form.get("pic")+"==").encode('utf-8')

        #get the username from the user
        username = request.form.get("name")

        #substitute that username into the database
        name = db.execute("SELECT * FROM users WHERE username = :username",
                        username=username)

        #if the username doesn't exist in the database display a message   
        if len(name) != 1:
            return render_template("webcam.html",message = 1)
        
        #assign id to the user
        id_ = name[0]['id']  
        #compress the encoded image  
        compressed_data = zlib.compress(encoded_image, 9) 
        
        uncompressed_data = zlib.decompress(compressed_data)
        
        #optimizing image by encoding it in base 64
        decoded_data = b64decode(uncompressed_data)
        
        #opening the image file through which user tried to log in
        new_image_handle = open('./static/face/unknown/'+str(id_)+'.jpg', 'wb')
        
        #writing the decoded data in the image file
        new_image_handle.write(decoded_data)

        #closing the image file
        new_image_handle.close()

        try:
            #try opening already present inages from which we have to match new inage
            image_of_bill = face_recognition.load_image_file(
            './static/face/'+str(id_)+'.jpg')
        except:
            #if no image is present in the face folder(login image goes in 'unknown' folder) that means no one registered yet
            return render_template("webcam.html",message = 5)

        #generate face encodings of knowm image that is already present in face folder
        bill_face_encoding = face_recognition.face_encodings(image_of_bill)[0]

        #load unknown image for facial recognisation
        unknown_image = face_recognition.load_image_file(
        './static/face/unknown/'+str(id_)+'.jpg')
        try:
            # try generating face encodings of unknown image
            unknown_face_encoding = face_recognition.face_encodings(unknown_image)[0]
        except:
            #if system is not able to generate encoding that means image is not clear hence display message
            return render_template("webcam.html",message = 2)


#  comparing faces using face encodings we generated earlier of known and unknown image

        #kept tolerance low to increase accuracy
        results = face_recognition.compare_faces(
        [bill_face_encoding], unknown_face_encoding,tolerance=0.5)

        #if result is true
        if results[0]:
            #check for the username
            username = db.execute("SELECT * FROM users WHERE username = :username",
                              username="swa")
            session["user_id"] = username[0]["id"]
            #if username and image matches 'display you have loded in'
            return render_template("index.html")
        else:
            #else display incorrect face
            return render_template("webcam.html",message=3)


    else:
        return render_template("webcam.html")


# when user choses to register his face
@app.route("/facesetup", methods=["GET", "POST"])
def facesetup():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #get the image we got from the webcam encoded
        encoded_image = (request.form.get("pic")+"==").encode('utf-8')

        #substitute that user_id into the database
        id_=db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]

         #compress the encoded image  
        compressed_data = zlib.compress(encoded_image, 9) 
        
        uncompressed_data = zlib.decompress(compressed_data)

        #optimizing image by encoding it in base 64
        decoded_data = b64decode(uncompressed_data)
        
        #opening the image file through which user tried to register
        new_image_handle = open('./static/face/'+str(id_)+'.jpg', 'wb')
        
        #writing the decoded data in the image file
        new_image_handle.write(decoded_data)

        #close the image file
        new_image_handle.close()

        #load unknown image for facial recognisation
        image_of_bill = face_recognition.load_image_file(
        './static/face/'+str(id_)+'.jpg')    
        try:
            #try generating face encodings for the new image
            bill_face_encoding = face_recognition.face_encodings(image_of_bill)[0]
        except:
            #if system is not able to generate face enodings that means image is not clear hence display message    
            return render_template("video.html",message = 1)
        #if face encodings are generated successfully that means user has completed all steps of registering 
        return render_template("final.html")

    else:
        return render_template("video.html")


# Handling the errors
def errorhandler(e):
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html",e = e)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

# run the main file
if __name__ == '__main__':
      app.run()
