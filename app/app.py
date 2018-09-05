from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from flask_mail import Mail, Message
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, IntegerField
from passlib.hash import sha256_crypt
from functools import wraps
from wtforms.fields.html5 import DateField
import datetime
import time
# from decorators import async
import smtplib
# from config import ADMINS
import os

now = datetime.datetime.today()

app = Flask(__name__)

app.config.update(
	DEBUG=True,
	#Email Settings
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME='jpisvideotest@gmail.com',
	MAIL_PASSWORD='Harshit18'
	)


mail = Mail(app)
	

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'secret'
app.config['MYSQL_DB'] = 'teacher_login'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MYSQL
mysql = MySQL(app)

# Index
@app.route('/')

def index():
    return render_template('index.html')


# Timetable
@app.route('/timetable')

def timetable():
    return render_template('timetable.html')

# Grades
@app.route('/grade')

def grades():
   #Create cursor
	cur = mysql.connection.cursor()

	#Get Tasks
	result = cur.execute("SELECT * FROM grades")

	grades = cur.fetchall()

	if result>0:
		return render_template('grade.html', grades=grades)
	else:
		msg = 'No Tasks Found'
		return render_template('grade.html', msg=msg)

	#Close Connection
	cur.close()

# Single Article
@app.route('/grades/<string:id>/')

def grade(id):
	#Create cursor
	cur = mysql.connection.cursor()

	#Get Tasks
	result = cur.execute("SELECT * FROM grades WHERE id=%s", [id])

	grades = cur.fetchone()

	return render_template('grades.html', grade = grades)

# Register Form Class
class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
			validators.DataRequired(),
			validators.EqualTo('confirm', message='Passwords do not match')
		])
	confirm = PasswordField('Confirm Password')

# User Register
@app.route('/register', methods=['GET', 'POST'])

def register():
	form = RegisterForm(request.form)
	if request.method == 'POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		# Create cursor
		cur = mysql.connection.cursor()

		# Execute query
		cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

		# Commit to DB
		mysql.connection.commit()

		# Close connection
		cur.close()

		flash('You are now registered and can log in', 'success')

		return redirect(url_for('login'))
	return render_template('register.html', form=form)

# User Login		
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		# Get Form Fields
		username = request.form['username']
		password_candidate = request.form['password']

		# Create cursor
		cur = mysql.connection.cursor()

		# Get user by username
		result = cur.execute("SELECT * FROM users WHERE username = %s", [username])

		if result > 0:
			# Get started hash
			data = cur.fetchone()
			password = data['password']

			# Compare Passwords
			if sha256_crypt.verify(password_candidate, password):
				# Passed
				session['logged_in'] = True
				session['username'] = username

				flash('You are now logged in', 'success')
				return redirect(url_for('mailing'))
			else:
				error = 'Invalid login'
				return render_template('login.html', error=error)
			# Close Connection
			cur.close()
		else:
			error = 'Username not found'
			return render_template('login.html', error=error)

	return render_template('login.html')

# Check if user logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorized, Please login', 'danger')
			return redirect(url_for('login'))
	return wrap


# Logout
@app.route('/logout')
@is_logged_in
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))


#Mailing
@app.route('/mailing', methods=['GET', 'POST'])
@is_logged_in
def mailing():
	#Create cursor
	cur = mysql.connection.cursor()

	#Get Tasks
	result = cur.execute("SELECT * FROM grades WHERE remind_date=%s", [now.strftime('%Y-%m-%d')])

	grades = cur.fetchone()

	result_1 = cur.execute("SELECT * FROM users WHERE username = %s", [grades['author']])

	users = cur.fetchone()

	if str(grades['remind_date']) == now.strftime('%Y-%m-%d'):
		msg = Message("Good Morning", sender="jpisvideotest@gmail.com", recipients=["%s", (str(users['email']))])
		msg.body = grades['body']
		mail.send(msg)
	
	# Close connection
	cur.close()
	return redirect(url_for('dashboard'))


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
	#Create cursor
	cur = mysql.connection.cursor()

	#Get Tasks
	result = cur.execute("SELECT * FROM grades")

	grades = cur.fetchall()

	if result>0:
		return render_template('dashboard.html', grades=grades)
	else:
		msg = 'No Tasks Found'
		return render_template('dashboard.html', msg=msg)

	#Close Connection
	cur.close()

# Grade Form Class
class GradeForm(Form):
	title = StringField('Title', [validators.Length(min=1, max=200)])
	body = TextAreaField('Body', [validators.required()])
	remind_date = DateField('Remind Date', [validators.required()], format = '%Y-%m-%d')

#Add Task
@app.route('/add_task', methods=['GET', 'POST'])
@is_logged_in
def add_task():
	form = GradeForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data
		remind_date = form.remind_date.data

		#Create Cursor
		cur = mysql.connection.cursor()

		#Execute
		cur.execute("INSERT INTO grades(title, body, author, remind_date) VALUES (%s, %s, %s, %s)", (title, body, session['username'], remind_date))

		#Commit to DB
		mysql.connection.commit()

		#Close connection
		cur.close()

		flash('Task Created', 'success')

		return redirect(url_for('dashboard'))

	return render_template('add_task.html', form=form)

#Edit Task
@app.route('/edit_task/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_task(id):

	#Create Cursor
	cur = mysql.connection.cursor()

	#Get task by id
	result = cur.execute("SELECT * FROM grades WHERE id=%s",[id])

	grades = cur.fetchone()

	#Get form
	form = GradeForm(request.form)

	#Populate tasks from fields
	form.title.data = grades['title']
	form.body.data = grades['body']
	form.remind_date.data = grades['remind_date']

	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']
		remind_date = request.form['remind_date']

		#Create Cursor
		cur = mysql.connection.cursor()

		#Execute
		cur.execute("UPDATE grades SET title=%s, body=%s, remind_date=%s WHERE id=%s", (title, body, remind_date, id))

		#Commit to DB
		mysql.connection.commit()

		#Close connection
		cur.close()

		flash('Task Updated', 'success')

		return redirect(url_for('dashboard'))

	return render_template('edit_task.html', form=form)

#Delete Tasks
@app.route('/delete_task/<string:id>', methods=['POST'])
@is_logged_in
def delete_task(id):
	# Create cursor
	cur = mysql.connection.cursor()

	# Execute
	cur.execute("DELETE FROM grades WHERE id = %s", [id])

	# Commit to DB
	mysql.connection.commit()

	# Close connection
	cur.close()

	flash('Task Deleted', 'success')

	return redirect(url_for('dashboard'))



if __name__ == '__main__':
	app.secret_key='secret123'
	app.run(debug=True)
