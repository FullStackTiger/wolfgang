# -*- coding: utf-8 -*-
"""Yacht picture route."""

from flask import Blueprint, send_from_directory

# from flask_jwt_extended import current_user

from wolfgang.cruise.yacht.models import YachtPicture


image_bp = Blueprint('img', __name__, url_prefix='/img')


@image_bp.route('/yacht/<filename>')
def yacht_picture(filename):
    """Pass uploaded picture through."""
    pic = YachtPicture.get_by(filename = filename, fail_ns = image_bp)
    print(pic.dir_path())
    return send_from_directory(pic.dir_path(), filename)
