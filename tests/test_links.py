import unittest
from unittest.mock import patch, MagicMock
import link_lens as app

class LinksTest(unittest.TestCase):
    def test_local_destination_rejected(self):
        with self.assertRaises(ValueError):
            app.validate_url('http://127.0.0.1/')
    def test_unsupported_scheme(self):
        self.assertEqual(app.check('file:///tmp/data')[1], '')
    @patch('link_lens.validate_url')
    @patch('link_lens.build_opener')
    def test_head_falls_back_on_405(self, make_opener, validate):
        response = MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.url = 'https://example.com/'
        error = app.HTTPError(response.url, 405, 'method', {}, None)
        make_opener.return_value.open.side_effect = [error, response]
        self.assertEqual(app.check(response.url)[1], 200)
        self.assertEqual(make_opener.return_value.open.call_args.args[0].get_method(), 'GET')
