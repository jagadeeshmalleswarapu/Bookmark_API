from flask import Flask, jsonify, redirect
from flask_jwt_extended import JWTManager
from BookmarkApi.src.auth import auth
from BookmarkApi.src.bookmarks import bookmarks
from BookmarkApi.src.database import db, Bookmark
from BookmarkApi.src.constants.http_status_codes import HTTP_404_NOT_FOUND, HTTP_500_INTERNAL_SERVER_ERROR
from flasgger import Swagger, swag_from
from BookmarkApi.src.config.swagger import template, swagger_config

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config["JWT_SECRET_KEY"] = "JWT_SECRET_KEY"




# @app.get('/')
# def index():
#     # db.create_all()
#     return 'Hello world!'
#
#
@app.get('/hello')
def hello():
    return jsonify({'message': 'hello world'})


db.app = app
db.init_app(app)

JWTManager(app)

app.register_blueprint(auth)

app.register_blueprint(bookmarks)

Swagger(app, config=swagger_config, template=template)


@app.get('/<short_url>')
@swag_from('./docs/short_url.yaml')
def redirect_to_url(short_url):
    bookmark = Bookmark.query.filter_by(short_url=short_url).first_or_404()

    if bookmark:
        bookmark.visits = bookmark.visits + 1
        db.session.commit()
        return redirect(bookmark.url)

@app.errorhandler(HTTP_404_NOT_FOUND)
def handle_404(e):
    return jsonify({'error': 'Not found'}), HTTP_404_NOT_FOUND

@app.errorhandler(HTTP_500_INTERNAL_SERVER_ERROR)
def handle_500(e):
    return jsonify({'error': 'Internal server error'}), HTTP_500_INTERNAL_SERVER_ERROR

if __name__ == '__main__':
    app.run(debug=True)
