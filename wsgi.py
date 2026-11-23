"""
TimetablePro - Production WSGI Entrypoint
Suitable for Gunicorn, Waitress, uWSGI, Render, Railway, PythonAnywhere, and Heroku.
"""
from app import app

if __name__ == '__main__':
    app.run()
