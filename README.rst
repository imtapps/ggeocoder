.. _geocoder_api:

**********************
Using the Geocoder API
**********************

.. _geocoding:

Geocoding
=========

To geocode an address, simply create a geocoder instance, and request a geocode. ::

  >>> g = Geocoder()
  >>> results = g.geocode('1600 Amphitheatre Pkwy')

If you want to provide any additional parameters that the Maps API accepts, send them
after the address.

  >>> g.geocode('Toledo', region='es', language='es', sensor='true')

See working_with_results_ for what to do next.

.. _reverse_geocoding:

Reverse Geocoding
=================

To do a reverse geocode, simply use the `reverse_geocode` method and provide lat/lng values

  >>> g = Geocoder()
  >>> results = g.reverse_geocode(37.4220827, -122.08289)

See working_with_results_ for what to do next.

.. _working_with_results:

Working with Results
====================

If the geocode is successful, you will have an object that is has
a list of geocoded results. You can check the number of results returned.
  >>> len(results)
  1

You can access each result by referencing its index in your result set.

  >>> first_result = results[0]
  
Once you have geocoded an address, it is very easy to work with.
There are a couple convenience methods for the GeoResult object.

The string representation will always be the formatted address.
You can also access formatted address directly, coordinates, and
a boolean check `is_valid_address` to see if the address is a valid street address.
Finally, there is a raw attribute which gives you access to the `raw` data returned
by the Google Maps API.


  >>> str(first_result)
  '1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA'

  >>> first_result.formatted_address
  u'1600 Amphitheatre Pkwy, Mountain View, CA 94043, USA'

  >>> first_result.coordinates
  (37.4220827, -122.08289)

  >>> first_result.is_valid_address
  True

The 'address_components' that the Maps API provides are made easily accessible by simple attribute lookups.

  >>> first_result.street_number
  u'1600'
  >>> first_result.postal_code
  u'94043'
  >>> first_result.country
  u'United States'

By default, the GeoResult will give you the 'long_name' of the address component. If you want the short name, just add it to your attribute lookup.

  >>> first_result.country__short_name
  u'US'
