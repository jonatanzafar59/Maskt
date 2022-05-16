from googleapiclient import discovery
from oauth2client.client import GoogleCredentials
import httplib2

class pxGcpConnector():
    def __init__(self):
        self.credentials = GoogleCredentials.get_application_default()
        self.service = discovery.build(
            'compute',
            'v1',
            credentials=self.credentials,
            cache_discovery=False,
            num_retries=3)

    def refresh(self):
        http = self.credentials.authorize(httplib2.Http())
        self.credentials.refresh(http)
