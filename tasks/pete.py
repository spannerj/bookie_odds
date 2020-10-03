from flask import Flask, request
app = Flask(__name__)


@app.route('/get_phone/', methods=['POST', 'GET'])
def get_phone():
    if request.method == 'POST':
        print('First name:', request.form['firstname'])
        print('Phone:', request.form['lastname'])

    return 'Take a look at your terminal!'


if __name__ == '__main__':
    app.run()
