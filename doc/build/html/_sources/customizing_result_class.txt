.. _customizing_result_class:

*************************************
Customizing the result class returned
*************************************

Customizing Result Class
========================

Sometimes you might want to interact with the results using your own custom class.
One particularly handy use case is giving the 'administrative_area...' items a more
friendly name for your context.

You can do this by subclassing the GeoResult class and providing an `attr_mapping` field.

We can create easy accessors to these pieces of data by doing something like the following::

  from ggeocoder import Geocoder, GeoResult

  class USGeoResult(GeoResult):
      attr_mapping = {
          'city': 'locality',
          'state': 'administrative_area_level_1',
          'county': 'administrative_area_level_2',
          'township': 'administrative_area_level_3',
          'ZIP': 'postal_code',
      }

  >>> g = Geocoder()
  >>> best_result = g.geocode('1600 Amphitheatre Pkwy', result_class=USGeoResult)[0]
  >>> best_result.state
  u'California'
  >>> best_result.state__short_name
  u'CA'
  >>> best_result.county
  u'Santa Clara'
  >>> best_result.city
  u'Mountain View'
  >>> best_result.ZIP
  u'94043'
  
