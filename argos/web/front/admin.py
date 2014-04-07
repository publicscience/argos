from argos.core import models

from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask.ext.security import roles_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

PER_PAGE = 20

@bp.route('/sources')
@roles_required('admin')
def sources():
    sources = models.Source.query.all()
    return render_template('admin/sources.jade', sources=sources)
