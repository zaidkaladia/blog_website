import firebase_admin
from firebase_admin import credentials, firestore
from flask import Flask, render_template, request, redirect, url_for, flash, session
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Firebase configuration
with open('firebase_config.json') as config_file:
    config = json.load(config_file)

# Initialize Firebase Admin SDK
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

# Admin credentials (in a real app, store these securely)
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin_password"

@app.route('/')
def home():
    posts = db.collection('posts').get()
    return render_template('visitor/home.html', posts=posts)

@app.route('/post/<post_id>')
def post(post_id):
    post = db.collection('posts').document(post_id).get().to_dict()
    return render_template('visitor/post.html', post=post)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials')
    return render_template('admin/login.html')


@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    posts = db.collection('posts').get()
    return render_template('admin/dashboard.html', posts=posts)


@app.route('/admin/create', methods=['GET', 'POST'])
def create_post():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = db.collection('posts').add({
            "title": title,
            "content": content,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/create_post.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('home'))



@app.route('/admin/delete/<post_id>', methods=['POST'])
def delete_post(post_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    # Delete the blog post from Firestore
    db.collection('posts').document(post_id).delete()
    flash('Post deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))




@app.route('/admin/edit/<post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    
    post_ref = db.collection('posts').document(post_id)
    post = post_ref.get()

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        post_ref.update({
            'title': title,
            'content': content,
            'last_edited': firestore.SERVER_TIMESTAMP
        })
        flash('Post updated successfully', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_post.html', post=post)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

