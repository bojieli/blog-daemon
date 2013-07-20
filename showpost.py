#!/usr/bin/env python2

from flask import Flask
from flask import request

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def hello():
    for k,v in request.form.iteritems():
        print k
        print '='*20
        print v
        print '.'
    return "hello"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
