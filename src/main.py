from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
import os
import glob
import configparser

config = configparser.ConfigParser()
config.read(os.path.abspath(os.path.join(os.path.dirname(__file__),'config.ini')))

db_dir = config['DEFAULT']['db_dir']
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), db_dir))  
links_on_home_page = config['DEFAULT']['links_on_home_page']
default_file_name = config['DEFAULT']['default_file_name']
valid_user = config['DEFAULT']['valid_user']
valid_password = config['DEFAULT']['valid_password']

app = Flask(__name__, static_folder='static')
app.secret_key = 'super secret key'  # Change this!

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, id):
        self.id = id


@login_manager.user_loader
def load_user(user_id):
    return User(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':   
        if request.form['username'] == valid_user and request.form['password'] == valid_password:
            user = User(request.form['username'])
            login_user(user)
            return redirect(url_for('add_link'))

    return render_template('login.html', title=config['DEFAULT']['title'])


def get_categories(path=''):
    absolute_path = os.path.join(base_dir, path)
    categories = sorted(os.listdir(absolute_path))
    folders = [category for category in categories if os.path.isdir(os.path.join(absolute_path, category))]
    return folders


def append_to_file(path, url, name, description):
    file_path = os.path.join(base_dir, path, default_file_name)

    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            file.write('| URL | Name | Description |\n')
    with open(file_path, 'a') as file:
        file.write(f'| {url} | {name} | {description} |\n')


@app.route('/add_link', methods=['GET', 'POST'])
@login_required
def add_link():
    message = None
    if request.method == 'POST':
        url = request.form['url']
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        try:
            append_to_file(category, url, name, description)
            message = 'Link added successfully'
        except Exception as e:
            message = f'Error: {e}'
    categories = get_categories()

    return render_template('add_link.html', categories=categories, message=message, title=config['DEFAULT']['title'])


@app.route('/')
def home():
    categories = sorted(os.listdir(base_dir))[:10]  # Get the first 10 categories

    data = []
    for category in categories:
        category_path = os.path.join(base_dir, category)
        md_files = sorted(glob.glob(os.path.join(category_path, '*.md')))

        links = []
        for md_file in md_files:
            with open(md_file, 'r') as file:
                for line in file:
                    row = [x.strip() for x in line.split('|')[1:-1]]  # Split by | and remove leading/trailing whitespace
                    if len(row) == 3 and row[0].startswith('http') and len(links) < int(links_on_home_page):  # Ensure the row has 3 elements (url, name, description)
                        links.append({
                            'url': row[0].strip(),
                            'title': row[1].strip(),
                            'description': row[2].strip()
                        })
        if len(links) > 0:
            data.append({
                'name': category,
                'links': links
            })

    return render_template('home.html', categories=data, title=config['DEFAULT']['title'])


@app.route('/<path:folder_path>')
def folder(folder_path):
    if folder_path == 'tree_view':
        folder_path = ''

    absolute_path = os.path.join(base_dir, folder_path)
    try:
        files = os.listdir(absolute_path)
    except FileNotFoundError:
        return 'Folder not found', 404
    files_and_folders = []
    for f in files:
        file_path = os.path.join(absolute_path, f)
        if os.path.isdir(file_path):
            files_and_folders.append({'name': f, 'path': os.path.join(folder_path, f), 'is_file': False})
        elif f.endswith('.md'):
            with open(file_path, 'r') as md_file:
                lines = md_file.readlines()  # Skip the header
            table = []
            for line in lines:
                row = [x.strip() for x in line.split('|')[1:-1]]  # Split by | and remove leading/trailing whitespace
                if len(row) == 3 and row[0].startswith('http'):  # Ensure the row has 3 elements (url, name, description)
                    table.append({'url': row[0], 'name': row[1], 'description': row[2]})
            files_and_folders.append({'name': f, 'path': os.path.join(folder_path, f), 'is_file': True, 'content': table})
    if folder_path :
        parent_folder = '/' + '/'.join(folder_path.split('/')[:-1]) if '/' in folder_path else '/tree_view'
    else:
        parent_folder = None
    files_and_folders = sorted(files_and_folders, key=lambda x: x['is_file'])
    return render_template('index.html', files_and_folders=files_and_folders, parent_folder=parent_folder, folder_path=folder_path, title=config['DEFAULT']['title'])

if __name__ == '__main__':
    app.run(host='0.0.0.0')