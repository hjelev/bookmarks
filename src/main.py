from flask import Flask, render_template, request
import os
import glob


app = Flask(__name__, static_folder='static')
db_dir = '../data'
base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), db_dir))  # base directory is the 'data' directory at the same level as the script's directory
links_on_home_page = 5  # Number of links to display on the home page


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
                    if len(row) == 3 and row[0].startswith('http') and len(links) < links_on_home_page:  # Ensure the row has 3 elements (url, name, description)
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

    return render_template('home.html', categories=data)

@app.route('/<path:folder_path>')
def folder(folder_path):
    if folder_path == 'tree_view':
        folder_path = ''

    absolute_path = os.path.join(base_dir, folder_path)
    print(absolute_path)
    files = os.listdir(absolute_path)
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
    return render_template('index.html', files_and_folders=files_and_folders, parent_folder=parent_folder, folder_path=folder_path)

if __name__ == '__main__':
    app.run(host='0.0.0.0')