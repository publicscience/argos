from argos.core import models
from argos.datastore import db
from argos.util.storage import save_from_file

from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask.ext.security import roles_required

from datetime import datetime

bp = Blueprint('admin', __name__, url_prefix='/admin')

PER_PAGE = 20

@bp.route('/sources')
@roles_required('admin')
def sources():
    sources = models.Source.query.order_by(models.Source.name).all()
    return render_template('admin/sources.jade', sources=sources)

@bp.route('/sources/<int:id>/icon', methods=['POST'])
def upload_sources_icon(id):
    if request.method == 'POST':
        source = models.Source.query.get(id)
        if source:
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = '{0}.{1}'.format(datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S-%f"), file.filename.rsplit('.', 1)[1])
                url = save_from_file(file, filename)

                source.icon = url
                db.session.commit()
                return url, 200
        else:
            return 'not found', 404

def allowed_file(filename, allowed_extensions=['png', 'jpg', 'jpeg', 'gif']):
    return '.' in filename and filename.rsplit('.', 1)[1] in allowed_extensions
