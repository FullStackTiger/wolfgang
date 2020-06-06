""" Client App """

from flask import Blueprint, render_template


client_bp = Blueprint('client_app', __name__,
                      url_prefix='',
                      static_url_path='/dist',
                      static_folder='./app/dist',
                      template_folder='.',
                      )


@client_bp.route('/', defaults={'path': ''})
@client_bp.route('/<path:path>')
def index(path):
    return render_template('index.html')
