#!/usr/bin/env python
"""
Web application for Testplan & Monitor UIs,
"""
from testplan.common.utils.path import pwd
from flask import Flask, send_from_directory, abort
from flask_restplus import Resource, Api
from werkzeug.exceptions import NotFound, NotImplemented
import argparse
import os

app = Flask(__name__)
_api = Api(app)

def parse_cli_args():
    """Web App command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--static-path', nargs='?', default=None, const=pwd())
    parser.add_argument('--data-path', nargs='?', default=None, const=pwd())
    return parser.parse_args()

@_api.route('/testplan/<string:report_uid>')
class Testplan(Resource):
    def get(self, report_uid):
        """Get a Testplan report (HTML) given it's uid."""
        directory = os.path.join(app.config['STATIC_PATH'], 'testing')
        return send_from_directory(directory=directory, filename='index.html')

@_api.route('/testplan/<string:report_uid>/report')
class TestplanReport(Resource):
    def get(self, report_uid):
        """Get a Testplan report (JSON) given it's uid."""
        directory = os.path.join(
            app.config['DATA_PATH'],
            'reports',
            'testplan_{uid}'.format(uid=report_uid)
        )
        return send_from_directory(directory=directory, filename='report.json')

@_api.route('/testplan/<string:report_uid>/assertions/<string:assertions_uid>')
class TestplanAssertions(Resource):
    def get(self, report_uid, assertions_uid):
        """Get an Assertion report (JSON) for a specific Testplan report given their uids."""
        raise NotImplemented()  # pylint: disable=notimplemented-raised

@_api.route('/testplan/<string:report_uid>/attachment/<string:attachment_uid>')
class TestplanAttachment(Resource):
    def get(self, report_uid, attachment_uid):
        """Get an attachment for a specific Testplan report given their uids."""
        raise NotImplemented()  # pylint: disable=notimplemented-raised

@_api.route('/testplan/static/<path:path>')
class TestplanStatic(Resource):
    def get(self, path):
        """Get static files for the Testplan UI."""
        directory = os.path.join(app.config['STATIC_PATH'], 'testing')
        if os.path.exists(os.path.join(directory, path)):
            return send_from_directory(directory=directory, filename=path)
        else:
            raise NotFound()

@_api.route('/monitor/<string:report_uid>')
class Monitor(Resource):
    def get(self, report_uid):
        """Get a Monitor report (HTML) given it's uid."""
        directory = os.path.join(app.config['STATIC_PATH'], 'monitor')
        return send_from_directory(directory=directory, filename='index.html')

@_api.route('/monitor/<string:report_uid>/report')
class MonitorReport(Resource):
    def get(self, report_uid):
        """Get a Monitor report (JSON) given it's uid."""
        directory = os.path.join(
            app.config['DATA_PATH'],
            'reports',
            'monitor_{uid}'.format(uid=report_uid)
        )
        return send_from_directory(directory=directory, filename='report.json')

@_api.route('/monitor/static/<path:path>')
class MonitorStatic(Resource):
    def get(self, path):
        """Get static files for the Monitor UI."""
        directory = os.path.join(app.config['STATIC_PATH'], 'monitor')
        if os.path.exists(os.path.join(directory, path)):
            return send_from_directory(directory=directory, filename=path)
        else:
            raise NotFound()

if __name__ == '__main__':
    args = parse_cli_args()

    if args.static_path:
        app.config['STATIC_PATH'] = args.static_path
    else:
        app.config['STATIC_PATH'] = pwd()
    if args.data_path:
        app.config['DATA_PATH'] = args.data_path
    else:
        # In future if not looking up data from the local file system
        # we will be looking it up from a database.
        app.config['DATA_PATH'] = pwd()

    print('Running Testplan web app on 0.0.0.0:5000...')
    app.run(host='0.0.0.0')
