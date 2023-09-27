import string
import random
from flask import Blueprint, request, jsonify
import validators
from BookmarkApi.src.constants.http_status_codes import (HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_204_NO_CONTENT,
                                                         HTTP_201_CREATED, HTTP_404_NOT_FOUND,
                                                         HTTP_409_CONFLICT)
from BookmarkApi.src.database import Bookmark, db
from flask_jwt_extended import get_jwt_identity, jwt_required
from flasgger import swag_from

bookmarks = Blueprint('bookmarks', __name__, url_prefix='/api/v1/bookmarks')


# In database.py this function is working, so I am directly using here
def generate_short_characters() -> str:
    characters = string.digits + string.ascii_letters
    picked_chars = ''.join(random.choices(characters, k=3))

    link = Bookmark.query.filter_by(short_url=picked_chars).first()
    if link:
        generate_short_characters()
    else:
        return picked_chars
    return picked_chars


@bookmarks.route('/', methods=['POST', 'GET'])
@jwt_required()
def bookmarksFun():
    current_user = get_jwt_identity()

    if request.method == 'POST':
        body = request.get_json().get('body', '')
        url = request.get_json().get('url', '')

        if not validators.url(url):
            return jsonify({
                'url': 'url is not valid'
            }), HTTP_400_BAD_REQUEST
        if Bookmark.query.filter_by(url=url).first():
            return jsonify({
                'error': 'url is already exists'
            }), HTTP_409_CONFLICT

        # characters = string.digits + string.ascii_letters
        # picked_chars = ''.join(random.choices(characters, k=3))
        #
        # link = Bookmark.query.filter_by(short_url=picked_chars).first()
        # if link:
        #
        # else:
        #     shortURL = picked_chars

        shortURL = generate_short_characters()
        bookmark = Bookmark(url=url, body=body, user_id=current_user, short_url=shortURL)
        db.session.add(bookmark)
        db.session.commit()

        return jsonify({
            'id': bookmark.id,
            'url': bookmark.url,
            'short_url': bookmark.short_url,
            'visits': bookmark.visits,
            'body': bookmark.body,
            'created_at': bookmark.created_at,
            'updated_at': bookmark.updated_at
        }), HTTP_201_CREATED

    else:
        # http://127.0.0.1:5000/api/v1/bookmarks/?page=2
        # http://127.0.0.1:5000/api/v1/bookmarks/?page=1&per_page=10
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        bookmark = Bookmark.query.filter_by(user_id=current_user).paginate(page=page, per_page=per_page)

        data = []
        for item in bookmark:
            data.append({
                'id': item.id,
                'url': item.url,
                'short_url': item.short_url,
                'visits': item.visits,
                'body': item.body,
                'created_at': item.created_at,
                'updated_at': item.updated_at
            })

        meta = {
            'page': bookmark.page,
            'pages': bookmark.pages,
            'total_count': bookmark.total,
            'prev_page': bookmark.prev_num,
            'next_page': bookmark.next_num,
            'has_next': bookmark.has_next,
            'has_prev': bookmark.has_prev
        }

        return jsonify({'data': data, 'meta': meta}), HTTP_200_OK


@bookmarks.get('/<int:id>')
@jwt_required()
def get_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()

    if not bookmark:
        return jsonify({
            'message': 'Item not found'
        }), HTTP_404_NOT_FOUND
    return jsonify({
        'id': bookmark.id,
        'url': bookmark.url,
        'short_url': bookmark.short_url,
        'visits': bookmark.visits,
        'body': bookmark.body,
        'created_at': bookmark.created_at,
        'updated_at': bookmark.updated_at
    }), HTTP_200_OK


@bookmarks.put('/<int:id>')
@bookmarks.patch('/<int:id>')
@jwt_required()
def edit_bookmark(id):
    current_user = get_jwt_identity()
    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()

    if not bookmark:
        return jsonify({
            'message': 'Item not found'
        }), HTTP_404_NOT_FOUND

    body = request.get_json().get('body', '')
    url = request.get_json().get('url', '')

    if not validators.url(url):
        return jsonify({
            'url': 'url is not valid'
        }), HTTP_400_BAD_REQUEST

    bookmark.url = url
    bookmark.body = body
    db.session.commit()

    return jsonify({
        'id': bookmark.id,
        'url': bookmark.url,
        'short_url': bookmark.short_url,
        'visits': bookmark.visits,
        'body': bookmark.body,
        'created_at': bookmark.created_at,
        'updated_at': bookmark.updated_at
    }), HTTP_200_OK


@bookmarks.delete('/<int:id>')
@jwt_required()
def delete_bookmark(id):
    current_user = get_jwt_identity()

    bookmark = Bookmark.query.filter_by(user_id=current_user, id=id).first()

    if not bookmark:
        return jsonify({
            'message': 'Item not found'
        }), HTTP_404_NOT_FOUND

    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({
        'message': 'Bookmark deleted successfully'
    }), HTTP_204_NO_CONTENT


@bookmarks.get('/stats')
@jwt_required()
@swag_from('./docs/bookmarks/stats.yaml')
def get_stats():
    current_user = get_jwt_identity()

    data = []
    items = Bookmark.query.filter_by(user_id=current_user).all()

    for item in items:
        new_link = {
            'visits': item.visits,
            'url': item.url,
            'id': item.id,
            'short_url': item.short_url
        }
        data.append(new_link)

    return jsonify({
        'data': data
    }), HTTP_200_OK

#
# @bookmarks.get('/')
# def get_all():
#     return {'Bookmarks': []}
