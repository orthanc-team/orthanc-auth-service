# Orthanc-share

Web service to run next to orthanc to handle sharing of studies by issuing [JWT](https://jwt.io/) that can then be passed
in authorization headers that will be checked by the [Authorization plugin](https://book.orthanc-server.com/plugins/authorization.html).

In order to use this image, you should define these environment variables or Docker secrets:
  - `SECRET_KEY` is a high entropy text that will be used to encode and decode the JWT
  - `PUBLIC_ORTHANC_ROOT` is the root url of the public Orthanc

Full sample setup will be available [here](https://github.com/orthanc-team/orthanc-share/tree/main/demo-setup).
