# -*- coding: utf-8 -*-
"""Contract routes."""

from http import HTTPStatus

from flask import current_app, Markup
from jinja2 import evalcontextfilter

import babel.dates
from flask import Blueprint, render_template
from flask_jwt_extended import current_user, jwt_required

from wolfgang.cruise.models import Cruise


# from wolfgang.user import permissions

contract_bp = Blueprint('contract', __name__, url_prefix='/contract', template_folder='templates')

@contract_bp.route('/draft/<cruise_id>')
@jwt_required
def draft(cruise_id):
    """Return formatted draft contract for cruise."""
    cruise = Cruise.get(cruise_id)
    if cruise is None:
        contract_bp.abort(HTTPStatus.NOT_FOUND)
    if not cruise.check_read_access(by_user = current_user):
        contract_bp.abort(HTTPStatus.UNAUTHORIZED)


    # from flask import Flask
    # from jinja2 import StrictUndefined
    # app = Flask(__name__)
    # app.jinja_env.undefined = StrictUndefined

    if len(cruise.waypoints) >= 2:
        waypoints = cruise.waypoints
    else:
        waypoints = [None, None]

    # TODO: check permissions etc
    missingDict = {'cruise':{}, 'yacht':{}, 'waypoints':[]}
    rendered = render_template('contract/contract.html',
                cruise=LogAllVars(missingDict['cruise'], cruise),
                yacht=LogAllVars(missingDict['yacht'], cruise.yacht),
                waypoints=LogAllVars(missingDict['waypoints'], waypoints)
                           )
    print('# Missing vars:')
    print(missingDict)

    return rendered
    # return render_template('contract/contract.html',
    #                        cruise=cruise,
    #                        fuel_price=cruise.fuel_price,
    #                        yacht=cruise.yacht,
    #                        waypoints=cruise.waypoints,
    #                        )

class LogAllVars:
    instance = None
    name = "ERROR"

    def __init__(self, missing_dict, instance, parent_missing_dict = None, counter = None):
        self.missing_dict = missing_dict
        # self.name = name
        self.instance = instance
        self.parent_missing_dict = parent_missing_dict
        self.counter = counter

    def __getitem__(self, idx):
        instance = super().__getattribute__('instance')
        missing_dict = super().__getattribute__('missing_dict')
        while len(missing_dict) <= idx:
            missing_dict.append({})
        return LogAllVars(missing_dict[idx], instance[idx])

    def __getattribute__(self, attr):
        instance = super().__getattribute__('instance')
        missing_dict = super().__getattribute__('missing_dict')
        # print("getattribute: {} {}".format(instance, attr))
        if instance is not None:
            val = instance.__getattribute__(attr)

            if attr in ['fuel_price']: # nested objects
                missing_dict[attr] = {}
                return LogAllVars(missing_dict[attr], val)
            elif val is not None:
                if attr in ['carriers', 'clients'] and list(val) == []:
                    missing_dict[attr] = {}
                    return [LogAllVars(missing_dict[attr], None)]
                elif attr in ['carriers', 'clients', 'stakeholders']:
                    missing_dict[attr] = []
                    return LogAllVars(missing_dict[attr], list(val))
                else:
                    return val

        # print("### Missing {}".format(attr))
        if not missing_dict.get(attr):
            missing_dict[attr] = True
        return MarkupPlus('<span class="missing">MISSING</span>')

    def __iter__(self):
        missing_dict = super().__getattribute__('missing_dict')
        instance = super().__getattribute__('instance')
        if len(missing_dict) == 0:
            missing_dict.append({})
        return LogAllVars(missing_dict[0], instance.__iter__(), missing_dict, 0)

    def __next__(self):
        parent_missing_dict = super().__getattribute__('parent_missing_dict')
        counter = super().__getattribute__('counter')
        instance = super().__getattribute__('instance')
        while len(parent_missing_dict) <= counter:
            missing_dict.append({})
        return LogAllVars(parent_missing_dict[counter], instance.__next__(), parent_missing_dict, counter)

    # def __getattr__(self, attr):
    #     print('{}: {}', self.name, attr)
    #     return self.object.__getattr__(attr)

# @contract_bp.app_template_filter('need_at_least_one')
# def need_at_least_one(val):
#     """Log if empty array."""
#     print("need_at_least_one")
#     print(val)
#     return val

# @contract_bp.app_template_filter('required')
# def required(val):
#     """Outputs a special marker if None and logs as missing."""
#     # TODO
#     return Markup('<span class="missing">MISSING</span>')

class MarkupPlus(Markup):
    @property
    def value(self):
        return self

    def __add__(self, val):
        return MarkupPlus('{}<span class="missing"> + {}</span>'.format(self, str(val)))
    def __sub__(self, val):
        return MarkupPlus('{}<span class="missing"> - {}</span>'.format(self, str(val)))
    def __mul__(self, val):
        return MarkupPlus('{}<span class="missing"> * {}</span>'.format(self, str(val)))
    def __div__(self, val):
        return MarkupPlus('{}<span class="missing"> / {}</span>'.format(self, str(val)))

    def __radd__(self, val):
        return MarkupPlus('<span class="missing">{} + </span>{}'.format(str(val), self))
    def __rsub__(self, val):
        return MarkupPlus('<span class="missing">{} - </span>{}'.format(str(val), self))
    def __rmul__(self, val):
        return MarkupPlus('<span class="missing">{} * </span>{}'.format(str(val), self))
    def __rdiv__(self, val):
        return MarkupPlus('<span class="missing">{} / </span>{}'.format(str(val), self))


@contract_bp.app_template_filter('count')
def count(sqla_obj):
    """Helper that forces loading of SQLAlchemy objects to get their length."""
    return len(list(sqla_obj))


@contract_bp.app_template_filter('s_if_many')
def s_if_many(sqla_obj):
    """Helper that returns 's' if more than one."""
    return 's' if(len(list(sqla_obj)) > 1) else ''


@contract_bp.app_template_filter('format_date')
def format_date(dt, format='full'):
    """Helper that formats dates appropriately."""
    if dt is None or dt.__class__ == MarkupPlus:
        return dt
    return babel.dates.format_date(dt, locale='en_GB', format=format)


@contract_bp.app_template_filter('format_datetime')
def format_datetime(dt, format='full'):
    """Helper that formats datetimes appropriately."""
    if dt is None or dt.__class__ == MarkupPlus:
        return dt
    return babel.dates.format_datetime(dt, locale='en_GB', format=format)

@contract_bp.app_template_filter('round')
def jinja_round(num, precision=0):
    """Helper that formats number appropriately."""
    if num is None or num.__class__ == MarkupPlus:
        return num
    return round(num, precision)
