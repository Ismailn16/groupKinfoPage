from flask import Flask, render_template, request, redirect, session, url_for
import os
from flask_mysqldb import MySQL
import MySQLdb.cursors
import MySQLdb.cursors, re, hashlib
import mysql.connector
from datetime import datetime
import time

app = Flask(__name__)
app.config['MYSQL_HOST'] = '127.0.0.1'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = os.environ.get('emailpageMySQL')
app.config['MYSQL_DB'] = 'emailpage'

mysql = MySQL(app)
app.secret_key = 'SecretKey'

@app.route('/home', methods=['GET', 'POST'])
@app.route('/')

def home():
    if 'loggedin' in session:
        username = session.get('username')
        firstTag = 'Dashboard'
        firstTagRoute = '/dashboard'
        secondTag = 'Log Out'
        secondTagRoute = '/logout'
        thirdTag = 'Profile'
        thirdTagRoute = '/profile'
        return render_template('index.html', username=username, firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, thirdTag=thirdTag, thirdTagRoute=thirdTagRoute)
    else:
        username = session.get('username')
        firstTag = 'Create Account'
        firstTagRoute = '/create_account_form'
        secondTag = 'Log In'
        secondTagRoute = '/login_function'
        return render_template('index.html', username=username, firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute)


@app.route('/create_account_form', methods = ['GET', 'POST'] )
def create_account_form():
    return render_template('create_account.html')

@app.route('/login_function', methods=['POST', 'GET'])
def login_function():
    return render_template('login.html')

@app.route('/create_account', methods=['POST'])
def create_account():
    msg = ''
    username = request.form['username']
    password = request.form['password']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE login_username = %s', (username,))
    account = cursor.fetchone()
    if account:
        msg = 'Account already exists!'
    elif not username or not password:
        msg = 'Please fill out the form!'
    else:
        cursor.execute('INSERT INTO users (login_username, login_password) VALUES (%s, %s)', (username, password))
        mysql.connection.commit()
        msg = 'You have successfully registered!'

    
    return render_template('create_account.html', msg=msg)


@app.route('/authenticate_user', methods=['POST', 'GET'])
def authenticate_user():
    username = request.form['username']
    password = request.form['password']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM users WHERE login_username = %s AND login_password = %s', (username, password,))
    account = cursor.fetchone()

    if account:

        session['loggedin'] = True
        session['user_id'] = account['userID']
        session['username'] = account['login_username']


        return redirect(url_for('dashboard'))
    else:
        msg = 'Incorrect username/password!'
        return render_template('login.html', msg=msg)
    

@app.route('/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   msg = 'You are now logged out'
   return render_template('login.html', msg=msg)

@app.route('/dashboard', methods={'GET', 'POST'})
def dashboard():
        userID = session.get('user_id')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM questions WHERE userID = %s', (userID,))
        myQuestionsData = cursor.fetchall()
        print(myQuestionsData)

        # Convert emaildata to a JSON serializable format
        myQuestionsArray = [dict(row) for row in myQuestionsData]

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM answers WHERE userID = %s', (userID,))
        myAnswersData = cursor.fetchall()

        myAnswersArray = [dict(row) for row in myAnswersData]

        # Save emailArray in session
        username = session.get('username')

        if myQuestionsArray == []:
            qMsg="You haven't asked a question yet :("
            if myAnswersArray == []:
                aMsg="You haven't answered anything yet :("
                return render_template('dashboard.html', username=username, qMsg=qMsg, aMsg=aMsg)
            else:
                return render_template('dashboard.html', username=username, qMsg=qMsg, myAnswersArray=myAnswersArray)   
        else: 
            if myAnswersArray == []:
                aMsg="You haven't answered anything yet :("
                return render_template('dashboard.html', username=username, myQuestionsArray=myQuestionsArray, aMsg=aMsg)
            else:
                return render_template('dashboard.html', username=username, myQuestionsArray=myQuestionsArray, myAnswersArray=myAnswersArray)   
        


@app.route('/profile', methods=['GET'])
def profile():
    userID = session.get('user_id')
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT login_username, login_password, first_name, last_name, UWE_email FROM users WHERE userID = %s', (userID,))
    profiledata = cursor.fetchall()

    if profiledata:
        row = profiledata[0]
        session['username'] = row['login_username']
        session['password'] = row['login_password']
        session['first_name'] = row['first_name']
        session['last_name'] = row['last_name']
        session['UWEemail'] = row['UWE_email']


    username = session.get('username')
    password = session.get('password')
    fName = session.get('first_name')
    lName = session.get('last_name')
    UWEemail = session.get('UWEemail')

    

    if fName is None:
        fName = 'No First Name Given'

    if lName is None:
        lName = 'No Last Name Given'

    if UWEemail is None:
        UWEemail = 'No UWE email Given'
    return render_template('profile.html', fName=fName, lName=lName, username=username, password=password, UWEemail=UWEemail)



@app.route('/modify_details', methods=['GET', 'POST'])
def modify_details_page():
    return render_template('modifySettings.html')






@app.route('/change_first', methods = ['GET'])
def change_first():
    First = 'New First Name'
    Second = 'Confirm New First Name:'
    verify = '/first_verify'
    message = session.pop('message', None)
    if message is None:
        return render_template('modifySettings.html', First=First, Second=Second, verify=verify)
    else:
        return render_template('modifySettings.html', First=First, Second=Second, verify=verify, message=message)

@app.route('/change_last', methods = ['GET'])
def change_last():
    First = 'New Last Name'
    Second = 'Confirm New Last Name:'
    verify = '/last_verify'
    message = session.pop('message', None)
    if message is None:
        return render_template('modifySettings.html', First=First, Second=Second, verify=verify)
    else:
        return render_template('modifySettings.html', First=First, Second=Second, verify=verify, message=message)

@app.route('/change_username', methods = ['GET'])
def change_username():
    First = 'Current Username:'
    Second = 'New Username:'
    verify = '/username_verify'
    message = session.pop('message', None)
    if message is None:
        return render_template('modifySettings.html', First=First, Second=Second, verify=verify)
    else:
        return render_template('modifySettings.html', First=First, Second=Second, verify=verify, message=message)

@app.route('/change_password', methods = ['GET'])
def change_password():
    First = 'Current Password:'
    Second = 'New Password:'
    verify = '/password_verify'
    message = session.pop('message', None)
    if message is None:
        return render_template('modifySettings.html', First=First, Second=Second, verify=verify)
    else:
        return render_template('modifySettings.html', First=First, Second=Second, verify=verify, message=message)

@app.route('/change_uwe', methods=['GET'])
def change_uwe():
    First = 'New UWE email:'
    Second = 'Confirm New UWE email:'
    verify = '/uwe_verify' 
    message = session.pop('message', None)
    if message is None:
        return render_template('modifySettings.html', First=First, Second=Second, verify=verify)
    else:
        return render_template('modifySettings.html', First=First, Second=Second, verify=verify, message=message)






@app.route('/first_verify', methods=['POST'])
def first_verify():
    userID = session.get('user_id')
    fName = session.get('first_name')
    first_entry = request.form['first_entry']
    last_entry = request.form['last_entry']
    print(fName)
    print(first_entry)
    print(last_entry)
    if fName == first_entry or fName == last_entry:
        session['message'] = 'Please type in a new First Name'
        return redirect(url_for('change_first'))
    elif first_entry == last_entry:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE users SET first_name = %s WHERE userID = %s', (first_entry, userID,))
        mysql.connection.commit()
        session['message'] = 'Your information has been updated!'
        return redirect(url_for('change_first'))
    else:
        session['message'] = 'Your entries no not match. Please re-enter the fields above.'
        return redirect(url_for('change_first'))

@app.route('/last_verify', methods = ['POST'])
def last_verify():
    userID = session.get('user_id')
    lName = session.get('last_name')
    first_entry = request.form['first_entry']
    last_entry = request.form['last_entry']
    if lName == first_entry or lName == last_entry:
        session['message'] = 'Please type in a new Last Name'
        return redirect(url_for('change_last'))
    elif first_entry == last_entry:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE users SET last_name = %s WHERE userID = %s', (first_entry, userID,))
        mysql.connection.commit()
        session['message'] = 'Your information has been updated!'
        return redirect(url_for('change_last'))
    else:
        session['message'] = 'Your entries no not match. Please re-enter the fields above.'
        return redirect(url_for('change_last'))

@app.route('/username_verify', methods = ['POST'])
def username_verify():
    userID = session.get('user_id')
    username = session.get('username')
    first_entry = request.form['first_entry']
    last_entry = request.form['last_entry']
    if username == first_entry:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE users SET login_username = %s WHERE userID = %s', (last_entry, userID,))
        mysql.connection.commit()
        session['message'] = 'Your information has been updated!'
        return redirect(url_for('change_username'))
    else:
        session['message'] = 'Your current username is incorrect. Please re-enter the fields above correctly.'
        return redirect(url_for('change_username'))

@app.route('/password_verify', methods = ['POST'])
def password_verify():
    userID = session.get('user_id')
    password = session.get('password')
    first_entry = request.form['first_entry']
    last_entry = request.form['last_entry']
    if password == first_entry:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE users SET login_password = %s WHERE userID = %s', (last_entry, userID,))
        mysql.connection.commit()
        session['message'] = 'Your information has been updated!'
        return redirect(url_for('change_password'))
    else:
        session['message'] = 'Your current password is incorrect. Please re-enter the fields above correctly.'
        return redirect(url_for('change_password'))

@app.route('/uwe_verify', methods = ['POST'])
def uwe_verify():
    userID = session.get('user_id')
    UWEemail = session.get('UWE_email')
    first_entry = request.form['first_entry']
    last_entry = request.form['last_entry']
    if '@live.uwe.ac.uk' in first_entry and last_entry:
        if UWEemail == first_entry or UWEemail == last_entry:
            session['message'] = 'Please type in a new UWE email'
            return redirect(url_for('change_uwe'))
        elif first_entry == last_entry:
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('UPDATE users SET UWE_email = %s WHERE userID = %s', (first_entry, userID,))
            mysql.connection.commit()
            session['message'] = 'Your information has been updated!'
            return redirect(url_for('change_uwe'))
        else:
            session['message'] = 'Your entries no not match. Please re-enter the fields above.'
            return redirect(url_for('change_uwe'))
    else:
        session['message'] = 'Please type in a UWE email'
        return redirect(url_for('change_uwe'))


@app.route('/qnaPage', methods=['GET'])
def qnaPage():

    topic = request.args.get('topic')

    if topic:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM questions WHERE questionTopic = %s", (topic,))
        questionsData = cursor.fetchall()
        questionsArray = [dict(row) for row in questionsData]
    else:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT * FROM questions")
        questionsData = cursor.fetchall()
        questionsArray = [dict(row) for row in questionsData]

    if 'loggedin' in session:
        username = session.get('username')
        firstTag = 'Dashboard'
        firstTagRoute = '/dashboard'
        secondTag = 'Log Out'
        secondTagRoute = '/logout'
        thirdTag = 'Profile'
        thirdTagRoute = '/profile'
        message = session.pop('message', None)
        if message is None:
            return render_template('q&aPage.html', username=username, firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, thirdTag=thirdTag, thirdTagRoute=thirdTagRoute, questionsArray=questionsArray)
        else:
            return render_template('q&aPage.html', username=username, firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, thirdTag=thirdTag, thirdTagRoute=thirdTagRoute, message=message, questionsArray=questionsArray)
    else:
        username = session.get('username')
        firstTag = 'Create Account'
        firstTagRoute = '/create_account_form'
        secondTag = 'Log In'
        secondTagRoute = '/login_function'
        message = session.pop('message', None)
        if message is None:
            return render_template('q&aPage.html', username=username, firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, questionsArray=questionsArray)
        else:
            return render_template('q&aPage.html', username=username, firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, message=message, questionsArray=questionsArray)

@app.route('/add_question', methods=['POST'])
def add_question():
    if 'loggedin' in session:
        userID = session.get('user_id')
        question = request.form['question']
        topic = request.form['topic']
        question_datetime = datetime.now()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('INSERT INTO questions (questionDesc, questionDT, questionTopic, userID) VALUES (%s, %s, %s, %s)', (question, question_datetime, topic, userID))
        mysql.connection.commit()
        session['message'] = 'Your question has been posted!'
        return redirect(url_for('qnaPage'))

@app.route('/question/<int:questionID>', methods=['GET'])
def question(questionID):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM questions WHERE questionID = %s", (questionID,))
    question = cursor.fetchone()

    cursor.execute("SELECT * FROM answers WHERE questionID = %s", (questionID,))
    answersData = cursor.fetchall()

    answersArray = [dict(row) for row in answersData]

        # Save emailArray in session
    session['answersArray'] = answersArray
    answersArray = session.get('answersArray')

    print(answersArray)

    if 'loggedin' in session:
        firstTag = 'Dashboard'
        firstTagRoute = '/dashboard'
        secondTag = 'Log Out'
        secondTagRoute = '/logout'
        thirdTag = 'Profile'
        thirdTagRoute = '/profile'
        message = session.pop('message', None)

        if message is None:
            if answersArray == []:
                msg="Wow, such empty:("
                return render_template('question.html', firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, thirdTag=thirdTag, thirdTagRoute=thirdTagRoute, question=question, msg=msg)
            else: 
                adt = 'Answer Date and Time'
                return render_template('question.html', firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, thirdTag=thirdTag, thirdTagRoute=thirdTagRoute, question=question, answersArray=answersArray, adt=adt)
        else:
            if answersArray == []:
                msg="Wow, such empty:("
                return render_template('question.html', firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, thirdTag=thirdTag, thirdTagRoute=thirdTagRoute, message=message, question=question, msg=msg)
            else: 
                adt = 'Answer Date and Time'
                return render_template('question.html', firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, thirdTag=thirdTag, thirdTagRoute=thirdTagRoute, message=message, question=question, answersArray=answersArray, adt=adt)
        
    else:
        firstTag = 'Create Account'
        firstTagRoute = '/create_account_form'
        secondTag = 'Log In'
        secondTagRoute = '/login_function'
        message = session.pop('message', None)
        
        if message is None:
            if answersArray == []:
                msg="Wow, such empty:("
                return render_template('question.html', firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, question=question, msg=msg)
            else: 
                adt = 'Answer Date and Time'
                return render_template('question.html', firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, question=question, answersArray=answersArray, adt=adt)
        else:
            if answersArray == []:
                msg="Wow, such empty:("
                return render_template('question.html', firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, message=message, question=question, msg=msg)
            else: 
                adt = 'Answer Date and Time'
                return render_template('question.html', firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, message=message, question=question, answersArray=answersArray, adt=adt)

@app.route('/add_answer/<int:questionID>', methods=['POST', 'GET'])
def add_answer(questionID):
    if 'loggedin' in session:
        userID = session.get('user_id')
        answer = request.form['answer']
        answer_datetime = datetime.now()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO answers (answerDesc, answerDT, userID, questionID) VALUES (%s, %s, %s, %s)", (answer, answer_datetime, userID, questionID))
        mysql.connection.commit()
        session['message'] = 'Your answer has been posted!'
        return redirect(url_for('question', questionID=questionID))
    else:
        session['message'] = "You need to be logged in to post an answer. If you don't have an account, please click 'Create Account' on the header"
        return redirect(url_for('question', questionID=questionID))

@app.route('/faqPage', methods=['GET'])
def faqPage():
    if 'loggedin' in session:
        username = session.get('username')
        firstTag = 'Dashboard'
        firstTagRoute = '/dashboard'
        secondTag = 'Log Out'
        secondTagRoute = '/logout'
        thirdTag = 'Profile'
        thirdTagRoute = '/profile'
        return render_template('faqPage.html', username=username, firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, thirdTag=thirdTag, thirdTagRoute=thirdTagRoute)
    else:
        username = session.get('username')
        firstTag = 'Create Account'
        firstTagRoute = '/create_account_form'
        secondTag = 'Log In'
        secondTagRoute = '/login_function'
        return render_template('faqPage.html', username=username, firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute)

@app.route('/faq/<pageName>')
def faq(pageName):
    if 'loggedin' in session:
        firstTag = 'Dashboard'
        firstTagRoute = '/dashboard'
        secondTag = 'Log Out'
        secondTagRoute = '/logout'
        thirdTag = 'Profile'
        thirdTagRoute = '/profile'
        return render_template(f'{pageName}.html', firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, thirdTag=thirdTag, thirdTagRoute=thirdTagRoute)
    else:
        firstTag = 'Create Account'
        firstTagRoute = '/create_account_form'
        secondTag = 'Log In'
        secondTagRoute = '/login_function'
        return render_template(f'{pageName}.html', firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute)


@app.route('/postQuestion', methods=['POST', 'GET'])
def postQuestion():
    if 'loggedin' in session:
        username = session.get('username')
        firstTag = 'Dashboard'
        firstTagRoute = '/dashboard'
        secondTag = 'Log Out'
        secondTagRoute = '/logout'
        thirdTag = 'Profile'
        thirdTagRoute = '/profile'
        return render_template('postQuestion.html', username=username, firstTag=firstTag, firstTagRoute=firstTagRoute, secondTag=secondTag, secondTagRoute=secondTagRoute, thirdTag=thirdTag, thirdTagRoute=thirdTagRoute)
    else:
        session['message'] = "You need to be logged in to post an answer. If you don't have an account, please click 'Create Account' on the header"
        return redirect(url_for('qnaPage'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)