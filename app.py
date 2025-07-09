from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import uuid
import os
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # For flash messages

# Database connection functio

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASS"),
            database=os.environ.get("DB_NAME"),
            port=int(os.environ.get("DB_PORT", 3306))
        )
        return connection
    except mysql.connector.Error as err:
        print("Error:", err)
        return None


@app.route('/')
def home():
    return render_template('index.html')

# User signup
@app.route('/user/signup', methods=['GET', 'POST'])
def user_signup():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Check if user already exists
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            flash('Email already exists! Please log in.')
            return redirect(url_for('user_login'))

        # Insert new user into the database
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, password))
        connection.commit()
        cursor.close()
        connection.close()

        flash('Signup successful! You can now log in.')
        return redirect(url_for('user_login'))

    return render_template('user_signup.html')

# User login
@app.route('/user/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user and user[2] == password:  # user[2] is the password column
            session['user_id'] = user[0]
            return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials. Please try again.')
        cursor.close()
        connection.close()

    return render_template('user_login.html')

# User dashboard
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' in session:
        return render_template('user_dashboard.html')
    return redirect(url_for('user_login'))

# Add fitness activity
@app.route('/user/add_activity', methods=['GET', 'POST'])
def add_activity():
    if 'user_id' in session:
        if request.method == 'POST':
            activity_name = request.form['activity_name']
            duration = request.form['duration']
            calories_burned = request.form['calories_burned']
            user_id = session['user_id']

            # Add activity to the database
            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO activities (user_id, activity_name, duration, calories_burned) VALUES (%s, %s, %s, %s)",
                           (user_id, activity_name, duration, calories_burned))
            connection.commit()
            cursor.close()
            connection.close()

            flash('Activity added successfully!')
            return redirect(url_for('user_dashboard'))

        return render_template('add_activity.html')
    return redirect(url_for('user_login'))

# View activities
@app.route('/user/view_activities')
def view_activities():
    if 'user_id' in session:
        user_id = session['user_id']
        connection = create_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM activities WHERE user_id = %s", (user_id,))
        activities = cursor.fetchall()
        cursor.close()
        connection.close()
        return render_template('view_activities.html', activities=activities)
    return redirect(url_for('user_login'))

@app.route('/user/view_progress')
def view_progress():
    if 'user_id' in session:
        user_id = session['user_id']
        connection = create_connection()
        cursor = connection.cursor()

        # Burned
        cursor.execute("SELECT SUM(calories_burned) FROM activities WHERE user_id = %s", (user_id,))
        total_burned = cursor.fetchone()[0] or 0

        # Consumed
        cursor.execute("SELECT SUM(calories_consumed) FROM meals WHERE user_id = %s", (user_id,))
        total_consumed = cursor.fetchone()[0] or 0

        cursor.close()
        connection.close()

        net_calories = total_consumed - total_burned

        return render_template('view_progress.html',
                               total_burned=total_burned,
                               total_consumed=total_consumed,
                               net_calories=net_calories)
    return redirect(url_for('user_login'))


@app.route('/user/add_meal', methods=['GET', 'POST'])
def add_meal():
    if 'user_id' in session:
        if request.method == 'POST':
            meal_name = request.form['meal_name']
            calories_consumed = request.form['calories_consumed']
            user_id = session['user_id']

            connection = create_connection()
            cursor = connection.cursor()
            cursor.execute("INSERT INTO meals (user_id, meal_name, calories_consumed) VALUES (%s, %s, %s)",
                           (user_id, meal_name, calories_consumed))
            connection.commit()
            cursor.close()
            connection.close()

            flash('Meal added successfully!')
            return redirect(url_for('user_dashboard'))

        return render_template('add_meal.html')
    return redirect(url_for('user_login'))

@app.route('/user/view_meals')
def view_meals():
    if 'user_id' in session:
        user_id = session['user_id']
        connection = create_connection()
        cursor = connection.cursor()
        
        # Get all meals for the logged-in user
        cursor.execute("SELECT * FROM meals WHERE user_id = %s", (user_id,))
        meals = cursor.fetchall()
        
        cursor.close()
        connection.close()

        return render_template('view_meals.html', meals=meals)
    
    return redirect(url_for('user_login'))



if __name__ == '__main__':
    app.run(debug=True)
