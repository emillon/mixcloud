Mixcloud.com API access from Python
-----------------------------------

|Build Status| |Coverage Status|

This provides a Python API for the http://mixcloud.com website.

Example
-------

.. code:: python

    from mixcloud import Mixcloud
    m = Mixcloud()
    u = m.user('michelplatiniste')
    for c in u.cloudcasts():
        print c.name

Authorization
-------------

You must have an application registered with Mixcloud and a corresponding
client ID and secret.

Authorization is a multi-step process:

1. Generate the authorization URL
2. Redirect the user to the URL to authorize your application
3. Collect the `code` query string parameter from the redirect
4. Exchange the code for an access token

.. code:: python

    o = mixcloud.MixcloudOauth(
        client_id=client_id, client_secret=client_secret,
        redirect_uri=redirect_uri)

    url = o.authorise_url()

    # Next redirect the user to `url`. They will be redirected to your
    # redirect uri with a `code` query string parameter. This must be
    # exchanged with Mixcloud for an access token.

    access_token = o.exchange_token(code)

    # This can then be used for calls that required authorization.

    m = mixcloud.Mixcloud(access_token=access_token)
    print(m.me())

Uploading
---------

It is possible to use this module to upload cloudcasts. In order to do
that you need to be authenticated. To do that, provide an API token to
the constructor.

.. code:: python

    m = mixcloud.Mixcloud(access_token=access_token)
    cc = Cloudcast(...)
    with open(mp3_path) as mp3:
        r = m.upload(cc, mp3)

YML file support
----------------

It is possible to represent cloudcasts as YAML files. See
``example.yml``.

The relevant keys are:

+----------+-------------------+
| Key      | Type              |
+==========+===================+
| title    | String            |
+----------+-------------------+
| desc     | String            |
+----------+-------------------+
| tags     | List of strings   |
+----------+-------------------+
| tracks   | List of tracks    |
+----------+-------------------+

Each track is a dict with the following keys:

+----------+-----------+
| Key      | Type      |
+==========+===========+
| start    | Integer   |
+----------+-----------+
| artist   | String    |
+----------+-----------+
| track    | String    |
+----------+-----------+

You can leverage YAML syntax for the "start" field: ``2:54`` will be
parsed directly as 174 (then number of seconds).

It is possible to parse such a file with:

.. code:: python

    with open(yml_path) as yml:
        cc = mixcloud.Cloudcast.from_yml(yml, None)

Mocking
-------

A mock server is provided for testing purposes in ``mixcloud.mock``.

.. |Build Status| image:: https://img.shields.io/travis/emillon/mixcloud/master.svg
   :target: http://travis-ci.org/emillon/mixcloud
.. |Coverage Status| image:: https://img.shields.io/coveralls/emillon/mixcloud/master.svg
   :target: https://coveralls.io/r/emillon/mixcloud
