import re
from datetime import datetime, timedelta

import jinja2
import humanize
from lxml.html.clean import clean_html

from flask import Blueprint, url_for
from flask.ext.security import current_user
from flask.ext import babel

bp = Blueprint('filters', __name__)

@bp.app_template_filter()
def natural_datetime(dt):
    """
    A template filter for rendering
    datetimes in human-readable form,
    e.g. "1 hour ago", "5 days ago", etc.

    Example usage (in `pyjade`)::

        div= event.updated_at|natural_datetime
    """
    return humanize.naturaltime(datetime.utcnow() - dt)

@bp.app_template_filter()
def natural_date(date):
    """
    A template filter for rendering
    dates in human-readable form,
    e.g. "5 days ago", etc.

    Example usage (in `pyjade`)::

        div= event.updated_at.date()|natural_date
    """
    dt = datetime.combine(date, datetime.min.time())
    diff = datetime.utcnow() - dt
    if diff <= timedelta(days=2):
        return humanize.naturalday(diff)
    return humanize.naturaltime(diff)

@bp.app_template_filter()
def format_date(date):
    format = 'MMMM d'
    dt = datetime.combine(date, datetime.min.time())
    if (datetime.utcnow() - dt).days > 365:
        format += ' y'
    return babel.format_date(date, format)

@bp.app_template_filter()
def format_currency(value, currency='USD'):
    if type(value) == str:
        value = int(value)
    return babel.format_currency(value, currency)

@bp.app_template_filter()
def highlight_mentions(text, mentions):
    """
    A template filter for highlighting
    mentions of concepts in a text.

    The mentions are first sorted by name length.
    """
    sorted_mentions = sorted(mentions, key=lambda x: len(x.name), reverse=True)
    for mention in sorted_mentions:
        text = re.sub(
                r' {name}(?!</a>)'.format(name=re.escape(mention.name)),
                ' <a href="{url}">{name}</a>'.format(
                    url=url_for('main.concept', slug=mention.slug),
                    name=mention.name),
                text)
    return text

@bp.app_template_filter()
def sanitize_html(html):
    """
    A template filter for
    sanitizing HTML.
    """
    # Wrap in jinja2.Markup so jinja doesn't
    # re-escape the html.
    return jinja2.Markup(clean_html(html))
