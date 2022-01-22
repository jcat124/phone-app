from flask import Flask, render_template
from flask_bootstrap import Bootstrap
import js2py

app = Flask(__name__)
bootstrap = Bootstrap(app)

# # this will translate example.js to example.py
# js2py.translate_file('static/sketch.js', 'sketch.py')
# # example.py can be now imported and used!


@app.route('/')
def home():
    return render_template('home.html')


if __name__ == '__main__':
    app.run(debug=True)
