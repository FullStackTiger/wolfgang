# -*- coding: utf-8 -*-
"""Waypoint resources."""
import datetime as dt
from http import HTTPStatus

from sqlalchemy import exc

from wolfgang.api import Resource
from wolfgang.api import cruise_ns as ns
from wolfgang.cruise.models import Cruise as CruiseModel
from wolfgang.database import db
from wolfgang.user import permissions
from wolfgang.utils import haversine

from . import parameters, schemas
from .models import Waypoint as WaypointModel


@ns.route('/<int:cruise_id>/waypoint/', methods=['GET', 'POST'])
@ns.param('cruise_id', 'Cruise identifier', sqla_model=CruiseModel)
class CruiseWaypoints(Resource):
    """Cruise-specific Waypoint operations."""

    @ns.permission_required(permissions.ReadAccessPermission, target_id='cruise_id')
    @ns.response(schemas.WaypointSchema(many=True))
    def get(self, cruise):
        """List current cruise waypoints."""
        return cruise.waypoints

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.parameters(parameters.WaypointParameters())
    @ns.response(schemas.WaypointSchema(many=True))
    def post(self, payload, cruise):
        """
        Add a single new waypoint.

        Automatically added to cruise. Returns list of waypoints for cruise.
        """
        try:
            selected_wp_id = payload.pop('selected_wp_id', None)
            if len(cruise.waypoints) == 0:
                payload['arr_date'] = dt.datetime.now()
            else:
                payload['arr_date'] = payload['arr_date'].replace(tzinfo=None)

                if selected_wp_id:
                    cur_wp = WaypointModel.get(selected_wp_id, fail_ns=ns)
                else:
                    cur_wp = cruise.waypoints[-1]
                cur_wp_idx = cruise.waypoints.index(cur_wp)

                delta = haversine(cur_wp.longitude, cur_wp.latitude,
                                  payload['longitude'], payload['latitude']) / 30
                payload['arr_date'] = cur_wp.arr_date + dt.timedelta(hours=delta)
                if cur_wp_idx < len(cruise.waypoints) - 1:
                    prev_dep_date = payload['arr_date']
                    prev_lon = payload['longitude']
                    prev_lat = payload['latitude']
                    for wp in cruise.waypoints[(cur_wp_idx + 1):]:
                        delta = haversine(prev_lon, prev_lat, wp.longitude, wp.latitude) / 30
                        increment = prev_dep_date + dt.timedelta(hours=delta) - wp.arr_date
                        if increment <= dt.timedelta(0):
                            break
                        wp.arr_date += increment
                        wp.dep_date += increment
                        wp.save()
                        prev_dep_date, prev_lon, prev_lat = wp.dep_date, wp.longitude, wp.latitude

            payload['dep_date'] = payload['arr_date']
            WaypointModel.create(version=cruise.version, cruise=cruise, **payload)
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT,
                     'Database Error: Could not create waypoint')
        return cruise.waypoints


@ns.route('/<int:cruise_id>/waypoint/<int:waypoint_id>', methods=['PUT', 'DELETE'])
@ns.param('cruise_id', 'Cruise identifier', sqla_model=CruiseModel)
@ns.param('waypoint_id', 'Waypoint identifier')
class Waypoint(Resource):
    """Waypoint-specific operations."""

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.parameters(parameters.EditWaypointParameters())
    @ns.response(schemas.WaypointSchema(many=True))
    def put(self, payload, cruise, waypoint_id):
        """
        Update existing waypoint.

        Uniquely identified by cruise_id and waypoint_id.
        Returns list of waypoints for cruise.
        """
        try:
            wp = WaypointModel.get(id=waypoint_id, version=cruise.version, fail_ns=ns)
            if wp.cruise_id != cruise.id:
                ns.abort(HTTPStatus.NOT_FOUND,
                         'Waypoint id {} does not belong to cruise id {}'.format(wp.id, cruise.id))
            if 'dep_date' in payload:
                payload['dep_date'] = payload['dep_date'].replace(tzinfo=None)
            if 'arr_date' in payload:
                payload['arr_date'] = payload['arr_date'].replace(tzinfo=None)

            if 'dep_date' in payload and 'arr_date' in payload:
                if payload['dep_date'] < payload['arr_date'] or not payload.get('is_call', True):
                    payload['dep_date'] = payload['arr_date']

            delta = payload.get('dep_date', wp.dep_date) - wp.dep_date

            if delta.total_seconds() > 1:
                print('Updating dates:')
                print(wp.dep_date)
                print(payload['dep_date'])
                wp_idx = cruise.waypoints.index(wp)
                if wp_idx < len(cruise.waypoints) - 1:
                    for wp in cruise.waypoints[(wp_idx + 1):]:
                        wp.arr_date += delta
                        wp.dep_date += delta
                        wp.save()
            wp.update(**payload)
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT,
                     'Database Error: Could not edit waypoint')
        return cruise.waypoints

    @ns.permission_required(permissions.WriteAccessPermission, target_id='cruise_id')
    @ns.response(code=HTTPStatus.NO_CONTENT, description='Waypoint deleted')
    @ns.response(code=HTTPStatus.CONFLICT, description='Cannot delete waypoint')
    def delete(self, cruise, waypoint_id):
        """
        Delete waypoint.

        Uniquely identified by cruise_id and waypoint_id.
        """
        # TODO: handle dis/emb
        w = WaypointModel.get(id=waypoint_id, version=cruise.version, fail_ns=ns)
        if w.cruise_id != cruise.id:
            ns.abort(HTTPStatus.NOT_FOUND, 'Waypoint id {} does not belong to cruise id {}'.format(w.id, cruise.id))

        try:
            w.delete()
        except exc.IntegrityError as e:
            db.session().rollback()
            ns.abort(HTTPStatus.CONFLICT,
                     'This waypoint cannot be deleted.')
        return '', HTTPStatus.NO_CONTENT
