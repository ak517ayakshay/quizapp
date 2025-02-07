from flask import Flask, render_template, redirect, url_for, session, flash,jsonify
from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField
from wtforms import SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, ValidationError
import bcrypt
from flask_mysqldb import MySQL
import MySQLdb
from flask import request, render_template, redirect, flash, url_for
from wtforms import StringField, PasswordField, SubmitField, IntegerField, DateTimeLocalField
from flask import Flask, request, render_template, redirect, url_for
from flask_mail import Mail, Message
import random
import string



app = Flask(__name__)

# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '12345678'
app.config['MYSQL_DB'] = 'quiz_app'
app.secret_key = 'akshaykumar'

mysql = MySQL(app)

class RegisterForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired()])
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    # print("Done till here")
    submit = SubmitField("Register")

    def validate_email(self,field):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where email=%s",(field.data,))
        user = cursor.fetchone()
        cursor.close()
        if user:
            raise ValidationError('Email Already Taken')

class LoginForm(FlaskForm):
    email = StringField("Email",validators=[DataRequired(), Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register',methods=['GET','POST'])
def register():
    
    form = RegisterForm()
    # print("Inside register   mannnnn")
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password = form.password.data
        # print("name",name)

        hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
        # print("email",email)

        # store  in database 
        cursor = mysql.connection.cursor()
        
        cursor.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)",(name,email,hashed_password))
        mysql.connection.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('register.html',form=form)


@app.route('/admincreation', methods=['GET', 'POST'])
def create_admin():
    form = RegisterForm()

    if form.validate_on_submit():
        try:
            # print("Kya hua")
            name = form.name.data
            email = form.email.data
            password = form.password.data

            # Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())

            cursor = mysql.connection.cursor()
            cursor.execute("INSERT INTO users (email, password, role) VALUES (%s, %s, %s)", 
                           (email, hashed_password, "admin"))
            mysql.connection.commit()
            cursor.close()
            # print("Yaha tak")

            return redirect(url_for('login'))  # Redirect to home or another page

        except Exception as e:
            flash(f"❌ Error: {str(e)}", "danger")

    return render_template("createadmin.html", form=form)


# @app.route('/login',methods=['GET','POST'])
# def login():
#     form = LoginForm()
#     if form.validate_on_submit():
#         email = form.email.data
#         password = form.password.data

#         cursor = mysql.connection.cursor()
#         cursor.execute("SELECT * FROM users WHERE email=%s",(email,))
#         user = cursor.fetchone()
#         cursor.close()
#         if user and bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
#             session['user_id'] = user[0]
#             return redirect(url_for('dashboard'))
#         else:
#             flash("Login failed. Please check your email and password")
#             return redirect(url_for('login'))

#     return render_template('login.html',form=form)





@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data.encode('utf-8')  # Ensure password is bytes

        # Use `with` to ensure cursor is closed properly
        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT id, email, password,role FROM users WHERE email=%s", (email,))
            user = cursor.fetchone()
            # print(user)

        if user and bcrypt.checkpw(password, user[2].encode('utf-8')):  # Ensure correct index for hashed password
            session['user_id'] = user[0]
            if user[3] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_tests'))
        else:
            flash("Login failed. Please check your email and password", "danger")
            return redirect(url_for('login'))

    return render_template('login.html', form=form)







@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        user_id = session['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users where id=%s",(user_id,))
        user = cursor.fetchone()
        cursor.close()


        if user:
            return render_template('dashboard.html',user=user)
            
    return redirect(url_for('login'))













@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash("You have been logged out successfully.")
    return redirect(url_for('login'))









class CreateTestForm(FlaskForm):
    name = StringField("Test Name", validators=[DataRequired()])
    num_questions = IntegerField("Number of Questions", validators=[DataRequired()])
    start_time = DateTimeLocalField("Start Time", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    end_time = DateTimeLocalField("End Time", format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    submit = SubmitField("Create Test")

@app.route('/create_test', methods=['GET', 'POST'])
def create_test():
    if 'user_id' not in session:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT role FROM users WHERE id=%s", (session['user_id'],))
    user_role = cursor.fetchone()
    cursor.close()

    if user_role and user_role[0] != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('user_tests'))

    form = CreateTestForm()

    if form.validate_on_submit():
        name = form.name.data
        num_questions = form.num_questions.data
        start_time = form.start_time.data
        end_time = form.end_time.data

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO tests (name, num_questions, start_time, end_time) VALUES (%s, %s, %s, %s)",
            (name, num_questions, start_time, end_time),
        )
        mysql.connection.commit()
        cursor.close()

        flash("✅ Test created successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('create_test.html', form=form)




class QuestionForm(FlaskForm):
    question_text = TextAreaField("Question", validators=[DataRequired()])
    option_1 = StringField("Option 1", validators=[DataRequired()])
    option_2 = StringField("Option 2", validators=[DataRequired()])
    option_3 = StringField("Option 3", validators=[DataRequired()])
    option_4 = StringField("Option 4", validators=[DataRequired()])
    correct_option = SelectField("Correct Option", choices=[("1", "Option 1"), ("2", "Option 2"), ("3", "Option 3"), ("4", "Option 4")], validators=[DataRequired()])
    difficulty = SelectField("Difficulty Level", choices=[("Easy", "Easy"), ("Medium", "Medium"), ("Hard", "Hard")], validators=[DataRequired()])
    submit = SubmitField("Add Question")

# @app.route('/add_questions', methods=['GET', 'POST'])
# def add_question():
#     if 'user_id' not in session:
#         flash("You need to be logged in as admin to add questions", "danger")
#         return redirect(url_for('login'))

#     cursor = mysql.connection.cursor()
#     cursor.execute("SELECT id, name FROM tests")
#     tests = cursor.fetchall()
#     cursor.close()

#     form = QuestionForm()
    
#     if request.method == 'POST' and form.validate_on_submit():
#         test_id = request.form.get("test_id")
#         question_text = form.question_text.data
#         option_1 = form.option_1.data
#         option_2 = form.option_2.data
#         option_3 = form.option_3.data
#         option_4 = form.option_4.data
#         correct_option = form.correct_option.data
#         difficulty = form.difficulty.data

#         cursor = mysql.connection.cursor()

#         cursor.execute("INSERT INTO questions (test_id, question_text, option_1, option_2, option_3, option_4, correct_option, difficulty) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
#                         (test_id, question_text, option_1, option_2, option_3, option_4, correct_option, difficulty))
#         mysql.connection.commit()
#         cursor.close()

#         flash("✅ Question added successfully!", "success")
#         return redirect(url_for('dashboard'))

#     return render_template("add_questions.html", form=form, tests=tests)










@app.route('/add_questions', methods=['GET', 'POST'])
def add_question():
    if 'user_id' not in session:
        flash("You need to be logged in as admin to add questions", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, name FROM tests where status='Pending'")
    tests = cursor.fetchall()
    cursor.close()

    form = QuestionForm()

    if request.method == 'POST' and form.validate_on_submit():
        test_id = request.form.get("test_id")
        question_text = form.question_text.data
        option_1 = form.option_1.data
        option_2 = form.option_2.data
        option_3 = form.option_3.data
        option_4 = form.option_4.data
        correct_option = form.correct_option.data
        difficulty = form.difficulty.data

        # Count the number of questions already created for this test
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM questions WHERE test_id = %s", (test_id,))
        current_question_count = cursor.fetchone()[0]
        
        # Get the required number of questions for the test
        cursor.execute("SELECT num_questions FROM tests WHERE id = %s", (test_id,))
        required_question_count = cursor.fetchone()[0]
        cursor.close()

        # Check if the required number of questions has been reached
        if current_question_count >= required_question_count:
            flash(f"❌ Required number of questions ({required_question_count}) have already been added for this test.", "danger")
            return redirect(url_for('add_question'))  # Stay on the same page

        # Insert the new question if the limit has not been reached
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO questions (test_id, question_text, option_1, option_2, option_3, option_4, correct_option, difficulty) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
                       (test_id, question_text, option_1, option_2, option_3, option_4, correct_option, difficulty))
        mysql.connection.commit()
        cursor.close()

        flash("✅ Question added successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template("add_questions.html", form=form, tests=tests)










# Flask-Mail Configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ak517ay@gmail.com'  # Change this
app.config['MAIL_PASSWORD'] = 'cdri gjmv uhgj ttvr'  # Change this securely
app.config['MAIL_DEFAULT_SENDER'] = 'ak517ay@gmail.com'  # Change this

mail = Mail(app)

# @app.route('/invite', methods=['GET', 'POST'])
# def invite():
#     if 'user_id' not in session:
#         flash("You need to login first", "danger")
#         return redirect(url_for('login'))
  

#     cursor = mysql.connection.cursor()
#     cursor.execute("SELECT role FROM users WHERE id=%s", (session['user_id'],))
#     user_role = cursor.fetchone()
#     cursor.close()

#     if not user_role or user_role[0] != 'admin':
#         flash("Unauthorized access!", "danger")
#         return redirect(url_for('dashboard'))

#     if request.method == 'POST':
#         email = request.form['email']
#         with mysql.connection.cursor() as cursor:
#             cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
#             existing_user = cursor.fetchone()
        
#         # Generate random password
#         if not existing_user:
#             random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
#             hashed_password = bcrypt.hashpw(random_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

#         # Store user in DB
#             cursor = mysql.connection.cursor()
#             cursor.execute("INSERT INTO users ( email, password,role) VALUES (%s, %s, %s)", 
#                        (email, hashed_password, "other"))
#             mysql.connection.commit()
#             cursor.close()

#         # Send email
#         try:
#             msg = Message("Quiz App Invitation", recipients=[email])
#             msg.body = f"""
#             Hello,

#             You have been invited to take a quiz on our platform.
            
#             Your login credentials:
#             Email: {email}

#            {f"Password: {random_password}" if not existing_user else "Use your existing password to login."}

#             Please login and change your password.

#             Regards,
#             Quiz Admin
#             """
#             mail.send(msg)
#             flash("✅ Invitation sent successfully!", "success")
#             return render_template("invite_form.html") 
#         except Exception as e:
#             flash(f"❌ Error sending email: {str(e)}", "danger")

#     return render_template("invite_form.html")



@app.route('/invite', methods=['GET', 'POST'])
def invite():
    if 'user_id' not in session:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT role FROM users WHERE id=%s", (session['user_id'],))
    user_role = cursor.fetchone()
    cursor.close()

    if not user_role or user_role[0] != 'admin':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('dashboard'))
    
   

    # Fetch all tests from the database
    with mysql.connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM tests WHERE status='Pending'")  # Assuming 'id' is the test ID and 'name' is the test name
        tests = cursor.fetchall()

    if request.method == 'POST':
        email = request.form['email']
        testId = request.form['test_id']  # The selected test_id from the form field

        cursor = mysql.connection.cursor()
        cursor.execute("""
        SELECT 
        t.id, 
        t.name, 
        t.num_questions, 
        COALESCE(q.total_created, 0) AS created_questions, 
        (t.num_questions - COALESCE(q.total_created, 0)) AS questions_left
        FROM tests t
        LEFT JOIN (
        SELECT 
            test_id, 
            COUNT(*) AS total_created
        FROM questions 
        GROUP BY test_id
    ) q ON t.id = q.test_id
    WHERE t.status = 'Pending' AND t.id = %s
    """, (testId,))

        checker = cursor.fetchone()
        cursor.close()

        print(checker)
        if checker and checker[4] != 0:
            flash(f'❌ All questions have not been added for this test. Please add {checker[4]} more questions.', "danger")

            return redirect(url_for('add_question'))


        with mysql.connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
            existing_user = cursor.fetchone()

        # Generate random password if user does not exist
        if not existing_user:
            random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            hashed_password = bcrypt.hashpw(random_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            with mysql.connection.cursor() as cursor:
                cursor.execute("INSERT INTO users (email, password, role) VALUES (%s, %s, %s)",
                               (email, hashed_password, "other"))
                mysql.connection.commit()

            # Fetch user ID of newly created user
            with mysql.connection.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
                user_id = cursor.fetchone()[0]
        else:
            user_id = existing_user[0]

        # Create the relationship between the user and the test in user_tests
        try:
            with mysql.connection.cursor() as cursor:
                cursor.execute("INSERT INTO user_tests (user_id, test_id) VALUES (%s, %s)", 
                               (user_id, testId))
                mysql.connection.commit()

            # Send email
            msg = Message("Quiz App Invitation", recipients=[email])
            msg.body = f"""
            Hello,

            You have been invited to take a quiz on our platform.
            
            Your login credentials:
            Email: {email}

            {f"Password: {random_password}" if not existing_user else "Use your existing password to login."}

            Please login and change your password.

            Regards,
            Quiz Admin
            """
            mail.send(msg)
            flash("✅ Invitation sent successfully!", "success")
            return render_template("invite_form.html", tests=tests)  # Pass tests to the template
        except Exception as e:
            flash(f"❌ Error creating relation or sending email: {str(e)}", "danger")

    return render_template("invite_form.html", tests=tests)  # Pass tests to the template






@app.route('/user_tests', methods=['GET'])
def user_tests():
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))

    # Fetch the logged-in user's ID from the session
    user_id = session['user_id']

    # Fetch the tests associated with the logged-in user
    with mysql.connection.cursor() as cursor:
        cursor.execute("""
            SELECT t.id, t.name, t.status
            FROM tests t
            JOIN user_tests ut ON t.id = ut.test_id
            WHERE ut.user_id = %s
        """, (user_id,))
        user_tests = cursor.fetchall()

    if not user_tests:
        flash("No tests found for this user.", "info")
        return render_template("user_tests.html", user_tests=[])

    return render_template("user_tests.html", user_tests=user_tests)














from datetime import datetime
from flask import redirect, url_for, flash, render_template

@app.route('/test/<int:test_id>', methods=['GET'])
def view_test(test_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']

    # Fetch the test details (start_time and end_time) from the database
    with mysql.connection.cursor() as cursor:
        cursor.execute("""
            SELECT name, start_time, end_time
            FROM tests
            WHERE id = %s
        """, (test_id,))
        test = cursor.fetchone()

    if not test:
        flash("Test not found.", "danger")
        return redirect(url_for('user_tests'))

    test_name, start_time, end_time = test
    current_time = datetime.now()

    # Check if current time is within test's start and end time
    if current_time < start_time or current_time > end_time:
        flash("You cannot access this test outside the allowed time window.", "danger")
        return redirect(url_for('user_tests'))

    # Fetch all the questions associated with the test
    with mysql.connection.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM questions
            WHERE test_id = %s
        """, (test_id,))
        questions = cursor.fetchall()

    # Check if the user has already completed the test
    with mysql.connection.cursor() as cursor:
        cursor.execute("""
        SELECT status
        FROM tests
        WHERE id = %s
        """, (test_id,))
        user_test_status = cursor.fetchone()

    # print(questions)
    if user_test_status and user_test_status[0] == 'Complete':
        flash("You have already completed this test.", "info")
        return redirect(url_for('user_tests'))

    return render_template('view_test.html', test_name=test_name, questions=questions, test_id=test_id)


# Middleware for auto-submit when test end time is reached
@app.before_request
def check_test_time():
    # Only apply to view_test and other test-related routes
    if request.endpoint not in ['view_test', 'submit_test']:
        return
    
    # Get the current time and compare with the test's end time
    with mysql.connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, end_time
            FROM tests
        """)
        tests = cursor.fetchall()

        current_time = datetime.now()

        for test in tests:
            test_id, end_time = test
            if current_time > end_time:
                # Auto-submit the test by updating the status in user_tests to 'Complete'
                cursor.execute("""
                    UPDATE tests
                    SET status = 'Complete'
                    WHERE id = %s
                """, (test_id,))
                mysql.connection.commit()
                # flash("Test submitted automatically. Time is up!", "warning")











@app.route('/submit_test/<int:test_id>', methods=['POST'])
def submit_test(test_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))

    user_id = session['user_id']
    answers = request.form

    # Fetch all the questions associated with the test
    with mysql.connection.cursor() as cursor:
        cursor.execute("""
            SELECT id FROM questions
            WHERE test_id = %s
        """, (test_id,))
        questions = cursor.fetchall()

    # Save answers to user_answers table
    for question in questions:
        question_id = question[0]
        selected_option = answers.get(f"answer_{question_id}")
        # print(selected_option)
        
        if selected_option:
            with mysql.connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO user_answers (user_id, test_id, question_id, selected_option)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, test_id, question_id, selected_option))

    # Update user_tests table to mark the test as 'Complete'
    # print(test_id)
    with mysql.connection.cursor() as cursor:
        cursor.execute("""
            UPDATE tests
            SET status = 'Complete'
            WHERE id = %s
        """, (test_id,))
        mysql.connection.commit()

    flash("Test submitted successfully!", "success")
    return redirect(url_for('user_tests'))










@app.route('/result/<int:test_id>', methods=['GET'])
def result(test_id):
    if 'user_id' not in session:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    
    # Fetch questions and user's selected answers
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT q.id, q.question_text, q.option_1, q.option_2, q.option_3, q.option_4, q.correct_option, 
               ua.selected_option
        FROM questions q
        JOIN user_answers ua ON q.id = ua.question_id
        WHERE ua.user_id = %s AND ua.test_id = %s
    """, (user_id, test_id))
    
    questions = cursor.fetchall()
    cursor.close()
    
    # Calculate marks
    total_marks = 0
    # print(questions) 
    for question in questions:
        # print(question[7]) 
        if question[7] == int(question[6]):  # Compare correct_option (casted to int) with selected_option
            total_marks += 1

    
    # Fetch test name for display
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT name FROM tests WHERE id = %s", (test_id,))
    test_name = cursor.fetchone()[0]
    cursor.close()

    return render_template('result.html', test_name=test_name, questions=questions, total_marks=total_marks)






# @app.route('/admin_dashboard', methods=['GET'])
# def admin_dashboard():
#     if 'user_id' not in session:
#         flash("You need to login first", "danger")
#         return redirect(url_for('login'))

#     # Check if the user is an admin
#     cursor = mysql.connection.cursor()
#     cursor.execute("SELECT role FROM users WHERE id=%s", (session['user_id'],))
#     user_role = cursor.fetchone()
#     cursor.close()

#     if not user_role or user_role[0] != 'admin':
#         flash("Unauthorized access!", "danger")
#         return redirect(url_for('dashboard'))

#     return render_template('admin_dashboard.html')



@app.route('/admin_dashboard', methods=['GET'])
def admin_dashboard():
    if 'user_id' not in session:
        flash("You need to login first", "danger")
        return redirect(url_for('login'))

    # Check if the user is an admin
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT role FROM users WHERE id=%s", (session['user_id'],))
    user_role = cursor.fetchone()
    
    if not user_role or user_role[0] != 'admin':
        cursor.close()
        flash("Unauthorized access!", "danger")
        return redirect(url_for('dashboard'))
    
    # Fetch all pending tests and count created questions
    cursor.execute("""
        SELECT 
            t.id, 
            t.name, 
            t.num_questions, 
            COALESCE(q.total_created, 0) AS created_questions, 
            (t.num_questions - COALESCE(q.total_created, 0)) AS questions_left
        FROM tests t
        LEFT JOIN (
            SELECT 
                test_id, 
                COUNT(*) AS total_created
            FROM questions 
            GROUP BY test_id
        ) q ON t.id = q.test_id
        WHERE t.status = 'Pending'
    """)
    pending_tests = cursor.fetchall()
    cursor.close()

    return render_template('admin_dashboard.html', pending_tests=pending_tests)






if __name__ == '__main__':
    app.run(debug=True)







