from flask import Flask, render_template, request, jsonify
import numpy as np
import pickle 
from flask import session, redirect, url_for
from flask_mysqldb import MySQL
from flask import flash, session, redirect, url_for, request, render_template


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# MySQL Configuration
app.config['MYSQL_HOST'] = '127.0.0.1'  # Use this instead of 'localhost'
app.config['MYSQL_USER'] = 'root'  # Your MySQL username
app.config['MYSQL_PASSWORD'] = 'Deekshitha1109$'  # Replace with your actual password
app.config['MYSQL_DB'] = 'disease_prediction'  # Use the correct database name
app.config['MYSQL_PORT'] = 3306  # Specify the port explicitly (optional)


mysql = MySQL(app)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
        user = cur.fetchone()
        cur.close()

        if user:
            session['user_id'] = user[0]
            flash("Login Successful")
            return redirect(url_for('home'))  # Redirect to home page
        else:
            flash("Invalid email or password. Please try again.")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            return "Passwords do not match!"

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (username, email, password))
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    return render_template("forgot_password.html")

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")

@app.route('/analysis')
def analysis():
    return render_template("analysis.html")

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route("/departments")
def departments():
    return render_template("departments.html")

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT disease, prediction_result, confidence, created_at 
        FROM predictions 
        WHERE user_id = %s 
        ORDER BY created_at DESC
    """, (user_id,))
    prediction_history = cur.fetchall()
    cur.close()

    return render_template("profile.html", history=prediction_history)


@app.route('/analysis/diabetes')
def analysis_diabetes():
    return render_template("analysis_diabetes.html")

@app.route('/analysis/heart')
def analysis_heart():
    return render_template("analysis_heart.html")

@app.route('/analysis/breast_cancer')
def analysis_breast_cancer():
    return render_template("analysis_breast_cancer.html")

@app.route('/analysis/liver')
def analysis_liver():
    return render_template("analysis_liver.html")

@app.route('/predict_heart')
def predict_heart():
    return render_template("predict_heart.html")

@app.route('/predict_diabetes')
def predict_diabetes():
    return render_template("predict_diabetes.html")

@app.route('/predict_breast_cancer')
def predict_breast_cancer():
    return render_template("predict_breast_cancer.html")

@app.route('/predict_liver')
def predict_liver():
    return render_template("predict_liver.html")

with open("rf_heart_model.pkl", "rb") as file:
    heart_model = pickle.load(file)

with open("pima_diabetes_model.pkl", "rb") as file:
    diabetes_model = pickle.load(file)

with open("liver_disease_model.pkl", "rb") as file:
    liver_model = pickle.load(file)

with open("breast_cancer_model.pkl", "rb") as file:
    cancer_model = pickle.load(file)

@app.route("/predict", methods=["POST"])
def predict():
    try:
        if 'user_id' not in session:
            return jsonify({"error": "User not logged in"})

        data = request.get_json()
        disease = data.get("disease", "").lower()
        user_id = session['user_id']  # Get the logged-in user's ID

        if disease == "heart":
            features = np.array([
                data["age"], data["sex"], data["cp"], data["trestbps"], data["chol"],
                data["fbs"], data["restecg"], data["thalach"], data["exang"],
                data["oldpeak"], data["slope"], data["ca"], data["thal"]
            ]).reshape(1, -1)
            model = heart_model
            result_message = ["✅ Low Risk of Heart Disease.", "⚠️ High Risk of Heart Disease!"]

        elif disease == "diabetes":
            features = np.array([
                data["pregnancies"], data["glucose"], data["blood_pressure"],
                data["skin_thickness"], data["insulin"], data["bmi"],
                data["dpf"], data["age"]
            ]).reshape(1, -1)
            model = diabetes_model
            result_message = ["✅ Low Risk of Diabetes.", "⚠️ High Risk of Diabetes!"]

        elif disease == "liver":
            features = np.array([
                data["age"], data["gender"], data["total_bilirubin"], data["direct_bilirubin"],
                data["alk_phosphate"], data["sgpt"], data["sgot"], data["total_protein"],
                data["albumin"], data["ag_ratio"]
            ]).reshape(1, -1)
            model = liver_model
            result_message = ["✅ Low Risk of Liver Disease.", "⚠️ High Risk of Liver Disease!"]

        elif disease == "cancer":
            features = np.array([
                data["Points Mean"], data["Symmetry Mean"], data["Fractal Dimension Mean"],
                data["Radius SE"], data["Texture SE"], data["Perimeter SE"], data["Area SE"],
                data["Smoothness SE"], data["Compactness SE"], data["Concavity SE"], data["Concave"]
            ]).reshape(1, -1)
            model = cancer_model
            result_message = ["✅ Low Risk of Breast Cancer.", "⚠️ High Risk of Breast Cancer!"]

        else:
            return jsonify({"error": "Invalid disease type. Choose from heart, diabetes, liver, or cancer."})

        # Prediction
        prediction = model.predict(features)[0]
        confidence = max(model.predict_proba(features)[0]) * 100
        result_text = result_message[prediction]

        # Save prediction to DB
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO predictions (user_id, disease, prediction_result, confidence)
            VALUES (%s, %s, %s, %s)
        """, (user_id, disease, result_text, round(confidence, 2)))
        mysql.connection.commit()
        cur.close()

        return jsonify({
            "prediction": result_text,
            "accuracy": round(confidence, 2)
        })

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(debug=True)


