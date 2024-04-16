from django.conf import settings
import os

from utils.test_utils import SpecTestCase

class DataTest(SpecTestCase):

    def test_data(self):
        response = self.get_request('/env/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data,  {'env': os.environ['AD_SUFFIX'], 'gen_pdf': settings.SOFFICE} )