"""Hello Analytics Reporting API V4."""

import argparse
import requests
import time
from datetime import timedelta, datetime
from apiclient.discovery import build
import httplib2
from oauth2client import client
from oauth2client import file
from oauth2client import tools

SCOPES = ['https://www.googleapis.com/auth/analytics.readonly']
DISCOVERY_URI = ('https://analyticsreporting.googleapis.com/$discovery/rest')
CLIENT_SECRETS_PATH = 'client_secrets.json' # Path to client_secrets.json file.
VIEW_ID = '' # change to your viewId
TG_CHAT_ID = '' # chat id
TG_ROBOT_TOKEN = '' # your robot id

gaNameMap = {'ga:users': 'users', 'ga:pageviews': 'pageviews', 'ga:deviceCategory': 'Device category'}


def initialize_analyticsreporting():
  """Initializes the analyticsreporting service object.

  Returns:
    analytics an authorized analyticsreporting service object.
  """
  # Parse command-line arguments.
  parser = argparse.ArgumentParser(
      formatter_class=argparse.RawDescriptionHelpFormatter,
      parents=[tools.argparser])
  flags = parser.parse_args([])

  # Set up a Flow object to be used if we need to authenticate.
  flow = client.flow_from_clientsecrets(
      CLIENT_SECRETS_PATH, scope=SCOPES,
      message=tools.message_if_missing(CLIENT_SECRETS_PATH))

  # Prepare credentials, and authorize HTTP object with them.
  # If the credentials don't exist or are invalid run through the native client
  # flow. The Storage object will ensure that if successful the good
  # credentials will get written back to a file.
  storage = file.Storage('analyticsreporting.dat')
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    credentials = tools.run_flow(flow, storage, flags)
  http = credentials.authorize(http=httplib2.Http())

  # Build the service object.
  analytics = build('analytics', 'v4', http=http, discoveryServiceUrl=DISCOVERY_URI)

  return analytics

def get_report(analytics):
  # Use the Analytics Service Object to query the Analytics Reporting API V4.
  return analytics.reports().batchGet(
      body={
        'reportRequests': [
        {
          'viewId': VIEW_ID,
          'dateRanges': [{'startDate': 'yesterday', 'endDate': 'yesterday'}],
          'metrics': [
            {'expression': 'ga:users'},
            {"expression": "ga:pageviews"},
          ],
          "orderBys":
          [
            {"fieldName": "ga:users", "sortOrder": "DESCENDING"},
          ],
          "dimensions":
          [
            {"name": "ga:deviceCategory"}
          ],
          "samplingLevel":  "LARGE"
        }]
      }
  ).execute()


def send_response(response):
  """Parses and prints the Analytics Reporting API V4 response"""
  tele_text = (datetime.today() + timedelta(-1)).strftime("%Y-%m-%d") + ' Info:' + '\n'
  for report in response.get('reports', []):
    columnHeader = report.get('columnHeader', {})
    dimensionHeaders = columnHeader.get('dimensions', [])
    metricHeaders = columnHeader.get('metricHeader', {}).get('metricHeaderEntries', [])
    rows = report.get('data', {}).get('rows', [])
    totals = report.get('data', {}).get('totals', [])
    # print totals[0].get('values')[0]
    tele_text = tele_text + '<pre>DAU: ' + totals[0].get('values')[0].encode("utf-8") + '</pre>'

    for row in rows:
      dimensions = row.get('dimensions', [])
      dateRangeValues = row.get('metrics', [])

      for header, dimension in zip(dimensionHeaders, dimensions):
        tele_text = tele_text + '<strong>' + (gaNameMap[header] or header) + ': ' + dimension + '</strong>\n'

      for i, values in enumerate(dateRangeValues):
        for metricHeader, value in zip(metricHeaders, values.get('values')):
          tele_text = tele_text + (gaNameMap[metricHeader.get('name')] or metricHeader.get('name')) + ': ' + value + '\n'
  print tele_text
  r = requests.get('https://api.telegram.org/bot' + TG_ROBOT_TOKEN + '/sendMessage?chat_id=' + TG_CHAT_ID + '&parse_mode=html&text=' + tele_text)

def main():
  analytics = initialize_analyticsreporting()
  response = get_report(analytics)
  send_response(response)

def timing():
  while True:
    now = datetime.now()
    if now.hour == 9 and now.minute == 50:
      main()
    time.sleep(20)


if __name__ == '__main__':
  # main()
  timing()