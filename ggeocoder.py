#!/usr/bin/env python
#

"""
Python library for using Google Geocoding API V3.
"""

import base64
import hashlib
import hmac
import urllib
import urllib2
import urlparse

try:
    import json
except ImportError:
    import simplejson as json


VERSION = '1.0.0'

__all__ = ['Geocoder', 'GeocoderResult', 'GeoResult',  'GeocodeError',]

class GeocodeError(Exception):
    """
    Base class for errors in the :mod:`ggeocoder` module.
        
    Methods of the :class:`Geocoder` raise this when the Google Maps API
    returns a status of anything other than 'OK'.
        
    See http://code.google.com/apis/maps/documentation/geocoding/index.html#StatusCodes
    for status codes and their meanings.
    """
    G_GEO_OK = "OK"
    G_GEO_ZERO_RESULTS = "ZERO_RESULTS"
    G_GEO_OVER_QUERY_LIMIT = "OVER_QUERY_LIMIT"
    G_GEO_REQUEST_DENIED = "REQUEST_DENIED"
    G_GEO_MISSING_QUERY = "INVALID_REQUEST"
        
    def __init__(self, status, url=None, response=None):
        """Create an exception with a status and optional full response.
                
        :param status: Either a ``G_GEO_`` code or a string explaining the
         exception.
        :type status: int or string
        :param url: The query URL that resulted in the error, if any.
        :type url: string
        :param response: The actual response returned from Google, if any.
        :type response: dict
                
        """
        super(GeocodeError, self).__init__(status)
        self.status = status
        self.url = url
        self.response = response
        
    def __str__(self):
        """Return a string representation of this :exc:`GeocoderError`."""
        return 'Error: {0}\nQuery: {1}'.format(self.status, self.url)
        
    def __unicode__(self, *args, **kwargs):
        """Return a unicode representation of this :exc:`GeocoderError`."""
        return unicode(self.__str__())

class GeoResult(object):
    """
    Represents the data for a single result returned by the google maps api.
    Allows you to access the data from the response using attributes instead
    of diving deep into the returned dictionary structure.

    You can create aliases for the default 'address_components' of the response
    by settings the `attr_mapping` field to a dict of your mapping.::
      attr_mapping = {'state': 'administrative_area_level_1'}
    """
    attr_mapping = None

    def __init__(self, data):
        self.data = data

    def __eq__(self, other):
        if isinstance(other, GeoResult):
            return self.data == other.data
        return False

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __unicode__(self):
        return self.formatted_address
    
    def __getattr__(self, name):
        lookup = name.split('__')
        attr = lookup[0]

        # customization can allow a mapping of attribute shortcuts to look up.
        if self.attr_mapping:
            attr = self.attr_mapping.get(attr, attr)

        try: prop = lookup[1]
        except IndexError: prop = 'long_name'

        for elem in self.data['address_components']:
            if attr in elem['types']:
                return elem[prop]
        else:
            message = "'{0}' does not have the attribute '{1}'".format(self.__class__.__name__, attr)
            raise AttributeError(message)

    @property
    def formatted_address(self):
        """returns fully formatted address result."""
        return self.data['formatted_address']

    @property
    def coordinates(self):
        """
        returns lat, lng coordinates as float types
        """
        loc = self.data['geometry']['location']
        return loc['lat'], loc['lng']

    @property
    def is_valid_address(self):
        """
        returns True when geocode result is a street address, False if not
        """
        return self.data['types'] == ['street_address']

    @property
    def raw(self):
        """
        Returns the raw dictionary object that the maps api returned
        for this single result.
        """
        return self.data



class GeocoderResult(object):
    """
    Helps process all the results returned from Google Maps API

    Can iterate over the results. Each unique result will be an
    instance of GeoResult.

    Example:
    results = GeocoderResult(data)
    for result in results:
        print result.formatted_address, result.coordinates

    You can also customize the result_class created if you'd like.

    """

    def __init__(self, data, result_class):
        self.data = [result_class(d) for d in data]

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


class Geocoder(object):
    """
    Interface for interacting with Google's Geocoding V3's API.
    http://code.google.com/apis/maps/documentation/geocoding/

    If you have a Google Maps Premier account, you can supply your
    client_id and private_key and the :class:`Geocoder` will make
    the request with a properly signed url
    """
    PREMIER_CREDENTIALS_ERROR = "You must provide both a client_id and private_key to use Premier Account."
    GOOGLE_API_URL = 'http://maps.googleapis.com/maps/api/geocode/json?'
    TIMEOUT_SECONDS = 3

    def __init__(self, client_id=None, private_key=None):
        """
        Google Maps API Premier users can provide credentials to make 100,000
        requests a day vs the standard 2,500 requests a day without

        client_id and private_key would have been provided to you when
        you received your initial Google Maps Premier account.

        :param client_id: client id for Premier account 'gme-youridentifier'
        :type client_id: str
        :param private_key: private key used to sign urls
        :type private_key: str

        """
        self.credentials = (client_id, private_key)
        if any(self.credentials) and not all(self.credentials):
            raise GeocodeError(self.PREMIER_CREDENTIALS_ERROR)

    def geocode(self, address, **params):
        """
        | Params may be any valid parameter accepted by Google's API.
        | http://code.google.com/apis/maps/documentation/geocoding/#GeocodingRequests
        """
        return self._get_geocoder_result(address=address, **params)

    def reverse_geocode(self, lat, lng, **params):
        """
        | Params may be any valid parameter accepted by Google's API.
        | http://code.google.com/apis/maps/documentation/geocoding/#GeocodingRequests
        """
        return self._get_geocoder_result(latlng="%s,%s" % (lat, lng), **params)

    @property
    def use_premier_key(self):
        return all(self.credentials)

    def _get_geocoder_result(self, result_class=GeoResult, **params):
        geo_params = {'sensor': 'false'} # API says sensor must always have a value
        geo_params.update(params)
        return GeocoderResult(self._get_results(params=geo_params), result_class)

    def _get_results(self, params=None):
        url = self._get_request_url(params or {})
        response = urllib2.urlopen(url, timeout=self.TIMEOUT_SECONDS)
        return self._process_response(response, url)

    def _process_response(self, response, url):
        j = json.load(response)
        if j['status'] != GeocodeError.G_GEO_OK:
            raise GeocodeError(j['status'], url)
        return j['results']

    def _get_request_url(self, params):
        encoded_params = urllib.urlencode(params)
        url = self.GOOGLE_API_URL + encoded_params
        if self.use_premier_key:
            url = self._get_premier_url(url)
        return url

    def _get_premier_url(self, base_url):
        client_id, private_key = self.credentials
        url_with_client = base_url + '&client=' + client_id

        url_signature = self._generate_signature(url_with_client, private_key)
        return url_with_client + '&signature=' + url_signature

    def _generate_signature(self, base_url, private_key):
        """
        http://code.google.com/apis/maps/documentation/webservices/index.html#PythonSignatureExample
        """
        url = urlparse.urlparse(base_url)
        url_to_sign = url.path + '?' + url.query
        decoded_key = base64.urlsafe_b64decode(private_key)
        signature = hmac.new(decoded_key, url_to_sign, hashlib.sha1)
        return base64.urlsafe_b64encode(signature.digest())


if __name__ == "__main__":
    import sys
    from optparse import OptionParser
        
    def main():
        """
        Geocodes a location given on the command line.
                
        Usage:
            ggeocoder.py "1600 amphitheatre mountain view ca" [YOUR_API_KEY]
            ggeocoder.py 37.4218272,-122.0842409 [YOUR_API_KEY]
                
        When providing a latitude and longitude on the command line, ensure
        they are separated by a comma and no space.
                
        """
        usage = "usage: %prog [options] address"
        parser = OptionParser(usage, version=VERSION)
        parser.add_option("-c", "--client_id",
                  dest="client_id", help="Your Google Maps Client Id key")
        parser.add_option("-k", "--private_key",
                  dest="private_key", help="Your Google Maps Private Signature key")
        (options, args) = parser.parse_args()
                
        if len(args) != 1:
            parser.print_usage()
            sys.exit(1)
                
        query = args[0]
        gcoder = Geocoder(options.client_id, options.private_key)
                
        try:
            result = gcoder.geocode(query)
        except GeocodeError, err:
            sys.stderr.write('%s\n%s\nResponse:\n' % (err.url, err))
            json.dump(err.response, sys.stderr, indent=4)
            sys.exit(1)
                
        for r in result:
            print r
            print r.coordinates
    main()
