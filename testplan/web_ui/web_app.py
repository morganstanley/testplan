from testplan.common.utils.path import pwd
from flask import Flask, send_from_directory
from flask_restplus import Resource, Api
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

@_api.route('/testplan_json/<string:report_uid>')
class TestplanJSON(Resource):
  def get(self, report_uid):
    """Get a Testplan report (JSON) given it's uid."""
    directory = os.path.join(
      app.config['DATA_PATH'],
      'reports',
      'testplan_{uid}'.format(uid=report_uid)
    )
    return send_from_directory(directory=directory, filename='report.json')

@_api.route('/monitor/<string:report_uid>')
class Monitor(Resource):
  def get(self, report_uid):
    """Get a Monitor report (HTML) given it's uid."""
    directory = os.path.join(app.config['STATIC_PATH'], 'monitor')
    return send_from_directory(directory=directory, filename='index.html')

@_api.route('/monitor_json/<string:report_uid>')
class MonitorJSON(Resource):
  def get(self, report_uid):
    """Get a Monitor report (JSON) given it's uid."""
    directory = os.path.join(
      app.config['DATA_PATH'],
      'reports',
      'monitor_{uid}'.format(uid=report_uid)
    )
    return send_from_directory(directory=directory, filename='report.json')

if __name__ == '__main__':
  args = parse_cli_args()

  if args.static_path:
    app.config['STATIC_PATH'] = args.static_path
  else:
    # In the future this will mean we are looking this information up from a database rather than the local filesystem?
    app.config['STATIC_PATH'] = pwd()
  if args.data_path:
    app.config['DATA_PATH'] = args.data_path
  else:
    # In the future this will mean we are looking this information up from a database rather than the local filesystem?
    app.config['DATA_PATH'] = pwd()

  app.run(host='0.0.0.0')
