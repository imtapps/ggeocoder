#!/usr/bin/env python

import mock
from io import StringIO
import unittest
from urllib.parse import urlencode

try:
    import json
except ImportError:
    import simplejson as json

from ggeocoder import Geocoder, GeoResult, GeocoderResult, GeocodeError

no_results_response = """{
   "results" : [],
   "status" : "ZERO_RESULTS"
}
"""
google_address_result = """{
   "results" : [
      {
         "address_components" : [
            {
               "long_name" : "1600",
               "short_name" : "1600",
               "types" : [ "street_number" ]
            },
            {
               "long_name" : "Amphitheatre Pkwy",
               "short_name" : "Amphitheatre Pkwy",
               "types" : [ "route" ]
            },
            {
               "long_name" : "Mountain View",
               "short_name" : "Mountain View",
               "types" : [ "locality", "political" ]
            },
            {
               "long_name" : "Santa Clara",
               "short_name" : "Santa Clara",
               "types" : [ "administrative_area_level_2", "political" ]
            },
            {
               "long_name" : "California",
               "short_name" : "CA",
               "types" : [ "administrative_area_level_1", "political" ]
            },
            {
               "long_name" : "United States",
               "short_name" : "US",
               "types" : [ "country", "political" ]
            },
            {
               "long_name" : "94043",
               "short_name" : "94043",
               "types" : [ "postal_code" ]
            }
         ],
         "formatted_address" : "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA",
         "geometry" : {
            "location" : {
               "lat" : 37.42182720,
               "lng" : -122.08424090
            },
            "location_type" : "ROOFTOP",
            "viewport" : {
               "northeast" : {
                  "lat" : 37.42317618029149,
                  "lng" : -122.0828919197085
               },
               "southwest" : {
                  "lat" : 37.42047821970849,
                  "lng" : -122.0855898802915
               }
            }
         },
         "types" : [ "street_address" ]
      }
   ],
   "status" : "OK"
}"""

class GeocodeErrorTests(unittest.TestCase):

    def test_geocode_error_string_representation_contains_error_and_query(self):
        status = 'ZERO_RESULTS'
        query_url = 'http://maps.googleapis.com/maps/api/geocode/json?address=thezoo'
        err = GeocodeError(status, url=query_url)
        self.assertEqual('Error: {0}\nQuery: {1}'.format(status, query_url), str(err))

    def test_geocode_error_raises_status_for_message(self):
        status = 'ZERO_RESULTS'
        query_url = 'http://maps.googleapis.com/maps/api/geocode/json?address=thezoo'

        with self.assertRaises(GeocodeError) as ctx:
            raise GeocodeError(status, url=query_url)
        self.assertEqual(status, ctx.exception.args[0])


class GeoResultTests(unittest.TestCase):

    def setUp(self):
        self.data = json.loads(google_address_result)['results'][0]
        self.result = GeoResult(self.data)

    def test_can_access_formatted_address_as_attribute(self):
        data = {'formatted_address': "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA"}
        result = GeoResult(data)
        self.assertEqual(data['formatted_address'], result.formatted_address)

    def test_uses_formatted_address_as_string_representation(self):
        data = {'formatted_address': "1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA"}
        result = GeoResult(data)
        self.assertEqual(data['formatted_address'], str(result))

    def test_is_valid_address_when_type_is_street_address(self):
        data = {'types': ['street_address']}
        result = GeoResult(data)
        self.assertTrue(result.is_valid_address)

    def test_is_not_valid_address_when_types_is_rural(self):
        data = {'types': ['route']}
        result = GeoResult(data)
        self.assertFalse(result.is_valid_address)

    def test_coordinates_property_returns_coordinates(self):
        self.assertEqual((37.42182720, -122.08424090), self.result.coordinates)

    def test_raw_property_returns_raw_data_for_result(self):
        result = GeoResult(self.data)
        self.assertEqual(self.data, result.raw)

    def test_uses_attributes_to_look_up_result_address_component_data(self):
        self.assertEqual("1600", self.result.street_number__long_name)

    def test_uses_long_name_for_attribute_lookup_by_default(self):
        self.assertEqual("United States", self.result.country)

    def test_can_lookup_by_short_name(self):
        self.assertEqual("US", self.result.country__short_name)

    def test_returns_none_when_doesnt_have_attribute(self):
        self.assertEqual(None, self.result.something)

    def test_two_geo_result_objects_are_equal_when_their_raw_data_is_equal(self):
        result_one = GeoResult(self.data)
        result_two = GeoResult(self.data)
        self.assertEqual(result_one, result_two)

    def test_two_geo_results_are_not_equal_when_other_is_not_geo_result_instance(self):
        result_one = GeoResult(self.data)
        self.assertNotEqual(result_one, self.data)

    def test_georesult_looks_up_attributes_with_attr_mapping_when_provided(self):
        class TestResult(GeoResult):
            attr_mapping = {
                'state': 'administrative_area_level_1',
                'ZIP': 'postal_code',
            }

        t = TestResult(self.data)
        self.assertEqual('94043', t.ZIP)
        self.assertEqual('California', t.state)
        self.assertEqual('CA', t.state__short_name)

    def test_custom_mapped_attrs_support_dunder_lookup(self):
        class TestResult(GeoResult):
            attr_mapping = {
                'state': 'administrative_area_level_1__short_name',
            }

        t = TestResult(self.data)
        self.assertEqual('CA', t.state)

        
class GeocoderResultTests(unittest.TestCase):

    def setUp(self):
        self.result_class = GeoResult
        self.data = [{
            'formatted_address': '4445 Corporate Dr, West Des Moines, IA 50266, USA',
        }, {
            'formatted_address': '1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA'
        }]

    def test_geocoder_result_gives_length_of_results_given(self):
        result = GeocoderResult(self.data, self.result_class)
        self.assertEqual(2, len(result))

    def test_converts_each_data_item_to_geo_result(self):
        result = GeocoderResult(self.data, self.result_class)

        self.assertEqual(GeoResult(self.data[0]), result.data[0])
        self.assertEqual(GeoResult(self.data[1]), result.data[1])

    def test_can_access_results_by_index(self):
        result = GeocoderResult(self.data, self.result_class)
        self.assertEqual(GeoResult(self.data[1]), result[1])

    def test_raises_index_error_when_doesnt_have_item_requested(self):
        result = GeocoderResult(self.data, self.result_class)
        with self.assertRaises(IndexError):
            result[2]
            
    def test_iterates_through_data_items_on_iter(self):
        result = GeocoderResult(self.data, self.result_class)
        self.assertEqual([GeoResult(self.data[0]), GeoResult(self.data[1])], list(result))


class GeocoderTests(unittest.TestCase):

    def setUp(self):
        self.private_key = 'vNIXE0xscrmjlyV-12Nj_BvUPaw='
        self.client_id = 'clientID'
        self.base_url = 'http://maps.googleapis.com/maps/api/geocode/json?address=New+York&sensor=false'
        self.known_signature = 'KrU1TzVQM7Ur0i8i7K3huiw3MsA=' # signature generated for above credentials

    def test_accepts_client_id_and_private_key_on_initialization(self):
        g = Geocoder(client_id=self.client_id, private_key=self.private_key)
        self.assertEqual((self.client_id, self.private_key), g.credentials)

    def test_raises_exception_when_client_id_provided_without_private_key(self):
        with self.assertRaises(GeocodeError) as ctx:
            Geocoder(client_id=self.client_id)
        msg = "You must provide both a client_id and private_key to use Premier Account."
        self.assertEqual(msg, ctx.exception.args[0])

    def test_raises_exception_when_private_key_provided_without_client_id(self):
        with self.assertRaises(GeocodeError) as ctx:
            Geocoder(private_key=self.private_key)
        msg = "You must provide both a client_id and private_key to use Premier Account."
        self.assertEqual(msg, ctx.exception.args[0])

    def test_allows_initialization_with_no_credentials(self):
        g = Geocoder()
        self.assertEqual((None, None), g.credentials)

    def test_use_premier_key_when_has_both_client_id_and_private_key(self):
        g = Geocoder(client_id=self.client_id, private_key=self.private_key)
        self.assertTrue(g.use_premier_key)

    def test_does_not_use_premier_key_when_neither_client_id_or_private_key(self):
        g = Geocoder()
        self.assertFalse(g.use_premier_key)

    def test_generate_signature_generates_proper_signature(self):
        # this is using a known signature from Google Documentation.
        # http://code.google.com/apis/maps/documentation/webservices/index.html#SignatureExamples
        g = Geocoder(client_id=self.client_id, private_key=self.private_key)
        base_url = self.base_url + '&client=clientID'
        self.assertEqual(self.known_signature, g._generate_signature(base_url, self.private_key))

    def test_get_premier_url_adds_client_and_signature_to_query_string(self):
        g = Geocoder(client_id=self.client_id, private_key=self.private_key)
        premier_url = g._get_premier_url(self.base_url)
        expected_url = self.base_url + '&client={0}&signature={1}'.format(self.client_id, self.known_signature)
        self.assertEqual(expected_url, premier_url)

    def test_get_request_url_returns_url_with_params_when_not_premier(self):
        params = dict(address='New York')

        g = Geocoder()
        request_url = g._get_request_url(params)

        self.assertEqual(g.GOOGLE_API_URL + urlencode(params), request_url)

    def test_get_request_url_returns_url_uses_api_key_when_present(self):
        params = dict(address='New York')

        g = Geocoder(api_key="FAKE-API-KEY")
        request_url = g._get_request_url(params)

        self.assertEqual(g.GOOGLE_API_URL + urlencode(params) + "&key=FAKE-API-KEY", request_url)

    def test_gets_premier_url_when_supplied_credentials(self):
        params = dict(address='New York', sensor="false")

        g = Geocoder(client_id=self.client_id, private_key=self.private_key)
        request_url = g._get_request_url(params)

        expected_url = g.GOOGLE_API_URL + urlencode(params) + '&client={0}&signature={1}'.format(self.client_id, self.known_signature)
        self.assertEqual(expected_url, request_url)
        
    @mock.patch.object(Geocoder, '_process_response', mock.Mock())
    @mock.patch('urllib.request.urlopen')
    @mock.patch.object(Geocoder, '_get_request_url')
    def test_get_results_opens_url_with_request_url_and_timeout(self, get_url, urlopen):
        params = dict(address='New York', sensor='false')
        
        g = Geocoder(client_id=self.client_id, private_key=self.private_key)
        g._get_results(params)
        get_url.assert_called_once_with(params)
        urlopen.assert_called_once_with(get_url.return_value, timeout=g.TIMEOUT_SECONDS)

    @mock.patch('urllib.request.urlopen')
    @mock.patch.object(Geocoder, '_get_request_url')
    @mock.patch.object(Geocoder, '_process_response')
    def test_get_results_returns_processed_response(self, process_response, get_url, urlopen):
        params = dict(address='New York', sensor='false')

        g = Geocoder(client_id=self.client_id, private_key=self.private_key)
        results = g._get_results(params)
        self.assertEqual(process_response.return_value, results)
        process_response.assert_called_once_with(urlopen.return_value, get_url.return_value)

    def test_process_response_raises_geocoder_error_when_status_not_ok(self):
        g = Geocoder()
        
        response = StringIO(no_results_response)
        url = 'http://www.example.com'
        with self.assertRaises(GeocodeError) as ctx:
            g._process_response(response, url)
        self.assertEqual(GeocodeError.G_GEO_ZERO_RESULTS, ctx.exception.status)
        self.assertEqual(url, ctx.exception.url)

    def test_process_response_returns_results_when_status_is_ok(self):
        success_json = """{
           "results" : [
              {"one": "the one"},
              {"two": "the two"}
           ],
           "status" : "OK"
        }"""
        response = StringIO(success_json)
        url = 'http://www.example.com'
        expected_result = [dict(one='the one'), dict(two='the two')]

        g = Geocoder()
        self.assertEqual(expected_result, g._process_response(response, url))

    @mock.patch('ggeocoder.GeocoderResult')
    @mock.patch.object(Geocoder, '_get_results')
    def test_geocode_returns_result_by_address_and_additional_params(self, get_results, geocoder_result_class):
        mock_result_class = mock.Mock()
        address = "1600 Amphitheatre Pkwy"
        result = Geocoder().geocode(address, sensor='true', result_class=mock_result_class)
        get_results.assert_called_once_with(params=dict(address=address, sensor='true'))
        geocoder_result_class.assert_called_once_with(get_results.return_value, mock_result_class)
        self.assertEqual(geocoder_result_class.return_value, result)

    @mock.patch('ggeocoder.GeocoderResult', mock.Mock(spec_set=GeocoderResult))
    @mock.patch.object(Geocoder, '_get_results')
    def test_geocode_adds_sensor_parameter_when_not_supplied(self, get_results):
        address = "1600 Amphitheatre Pkwy"

        Geocoder().geocode(address)
        get_results.assert_called_once_with(params=dict(address=address, sensor='false'))

    @mock.patch('ggeocoder.GeocoderResult')
    @mock.patch.object(Geocoder, '_get_results')
    def test_reverse_geocode_returns_result_by_latlng_and_additional_params(self, get_results, geocoder_result_class):
        lat, lng = 37.421827, -122.084241

        mock_result_class = mock.Mock()

        result = Geocoder().reverse_geocode(lat, lng, sensor='true', language='fr', result_class=mock_result_class)
        get_results.assert_called_once_with(params=dict(latlng='37.421827,-122.084241', sensor='true', language='fr'))
        geocoder_result_class.assert_called_once_with(get_results.return_value, mock_result_class)
        self.assertEqual(geocoder_result_class.return_value, result)

    @mock.patch('ggeocoder.GeocoderResult', mock.Mock(spec_set=GeocoderResult))
    @mock.patch.object(Geocoder, '_get_results')
    def test_reverse_geocode_adds_sensor_parameter_when_not_supplied(self, get_results):
        lat, lng = 37.4218270, -122.0842409

        Geocoder().reverse_geocode(lat, lng)
        get_results.assert_called_once_with(params=dict(latlng='37.421827,-122.0842409', sensor='false'))


if __name__ == "__main__":
    unittest.main()
