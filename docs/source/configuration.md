# Configuration

Environment variables without a default value are required to be set.

## Root `.env`

### Database Settings

These settings are used to set up the DB in the portfolio-postgres container.

#### `PORTFOLIO_DB_NAME`

Name of the PostgreSQL database.

```{note}
If you are running the development server locally ensure it has the same value as [`POSTGRES_DB`](./configuration.md#postgres_db) in django's `.env`.
```

#### `PORTFOLIO_DB_USER`

User of the PostgreSQL database.

```{note}
If you are running the development server locally ensure it has the same value as [`POSTGRES_USER`](./configuration.md#postgres_user) in django's `.env`.
```

#### `PORTFOLIO_DB_PASSWORD`

Password for user of the PostgreSQL database.

Make sure to change this to a strong password on any production/public server.

```{note}
If you are running the development server locally ensure it has the same value as [`POSTGRES_PASSWORD`](./configuration.md#postgres_password) in django's `.env`.
```

### Nginx Development Settings

If you are running nginx in development mode via the configuration of `docker-compose.override.dev.nginx.yml` you have to set the following variables:

#### `PORTFOLIO_FRONTEND`

This is the path to the (static/built) frontend files that nginx will serve.

#### `PORTFOLIO_ASSETS`

Folder for django's additional asset files (static and (protected) media files)

## django `.env`

The django `.env` file is located in `src/portfolio/.env`.

### `ACTIVE_SCHEMAS`

Default: All schemas defined in `src/core/schemas/entries/`

If you only want to use a subset of the included schemas, provide a list here.

```{warning}
Changing this value can lead to incompatibilities with other Portfolios and Showroom.
```

### `ALLOWED_HOSTS`

Default: `urlparse(SITE_URL).hostname`

The accepted HTTP Host headers, django will serve.

### `ANGEWANDTE_API_KEY`

Default: `''`

The API key for the base API of Angewandte.

### `BEHIND_PROXY`

Default: `True`

If you are running Portfolio behind nginx, this has to be `True`. For local development, set this to `False`.

### `CAS_CHECK_NEXT`

Default: `True`

If you want to use a non-local `CAS_REDIRECT_URL`, e.g. when redirecting to the frontend in a development setup, set this to `True`.

### `CAS_REDIRECT_URL`

Default: `FORCE_SCRIPT_NAME` if defined, else `/`

Wherever the CAS server should redirect to after successful auth.

### `CAS_RENAME_ATTRIBUTES`

Default: `{}`

A dict used to rename the attributes that the CAS server returns.

For example, if `CAS_RENAME_ATTRIBUTES=fn=first_name,ln=last_name` the `fn` and `ln` attributes returned by the CAS
server will be renamed to `first_name` and `last_name`.

Portfolio Backend expects the following attributes: `first_name`, `last_name`, `display_name` and `email`

### `CAS_SERVER`

Default: `f'{SITE_URL}cas/`

The base url for the CAS server, e.g. `https://your.base.domain/cas/`.

### `CAS_VERIFY_CERTIFICATE`

Default: `True`

Whether to allow only CA-signed certificates. Only set this to `False` for a local dev environment if your (local) CAS server is using a self-signed certificate.

### `CAS_VERSION`

Default: `3`

The CAS protocol version to use. Recommended is to use Version `2` or `3`.

### `CORS_ALLOWED_ORIGINS`

Default: `[]`

See https://github.com/adamchainz/django-cors-headers#cors_allowed_origins for further details.

### `CORS_ALLOW_ALL_ORIGINS`

Default: `False`

See https://github.com/adamchainz/django-cors-headers#cors_allow_all_origins for further details.

### `CORS_ALLOW_CREDENTIALS`

Default: `False`

See https://github.com/adamchainz/django-cors-headers#cors_allow_credentials for further details.

### `CSRF_COOKIE_DOMAIN`

Default: `None`

The domain that should be used for the CSRF cookies. Leave empty for a standard domain cookie.

See https://docs.djangoproject.com/en/2.2/ref/settings/#csrf-cookie-domain for further details.

### `CSRF_TRUSTED_ORIGINS`

Default: `[]`

A list of hosts which are trusted origins for unsafe requests.

See https://docs.djangoproject.com/en/2.2/ref/settings/#csrf-trusted-origins for further details.

### Database settings

#### `POSTGRES_DB`

Default: `django_portfolio`

Name of the PostgreSQL database name.

```{note}
If you are running the development server locally ensure it has the same value as [`PORTFOLIO_DB_NAME`](./configuration.md#portfolio_db_name) in root `.env`.
```

#### `POSTGRES_USER`

Default: `django_portfolio`

User of the PostgreSQL database.

```{note}
If you are running the development server locally ensure it has the same value as [`PORTFOLIO_DB_USER`](./configuration.md#portfolio_db_user) in root `.env`.
```

#### `POSTGRES_PASSWORD`

Default: `password_portfolio`

Password for user of the PostgreSQL database.

Make sure to change this to a strong password on any production/public server.

```{note}
If you are running the development server locally ensure it has the same value as [`PORTFOLIO_DB_PASSWORD`](./configuration.md#portfolio_db_password) in root `.env`.
```

#### `POSTGRES_PORT`

Default: `5432`

Port of the PostgreSQL database.

The database port only needs to be changed, if you are running Portfolio
locally in combination with e.g. Showroom also running locally. Then at
least one of the database container ports needs to be mapped to a different
value. So use whatever you set in your docker-compose.override.yml for
portfolio-postgres or use the default.

### `DEBUG`

Default: `False`

Sets djano's `DEBUG` setting. For development this can be set to `True`.

See https://docs.djangoproject.com/en/2.2/ref/settings/#debug for further details.

### `DJANGO_ADMIN_PATH`

Default: `admin`

The relative path for the Django admin interface.

### `DJANGO_ADMINS`

Default: `None`

Set up admin e-mail notifications.

### `DJANGO_SUPERUSERS`

Default: `()`

Define django superusers. Has to correspond to the user ids provided by the CAS server.

### `DOCKER`

Default: `True`

If you are developing locally (with django not running inside a container), set this to `False`.

### Documentation Settings

It's possible to serve the Sphinx documentation in `docs` directly via Django.
The access is protected via Basic Authentication, so both `DOCS_USER` and `DOCS_PASSWORD` have to be set.

#### `DOCS_URL`

Default: `docs/`

The URL where to host the documentation.

#### `DOCS_USER`

Default: `None`

The Basic Authentication user for the documentation.

#### `DOCS_PASSWORD`

Default: `None`

The Basic Authentication password for the documentation.

### E-Mail Settings

If you want to receive E-Mail notifications in case of an error, define `DJANGO_ADMINS` and the following E-Mail settings.

#### `EMAIL_HOST`

Default: `localhost`

The host to use for sending E-Mail.

#### `EMAIL_HOST_USER`

Default: `''`

Username to use for the SMTP server.

#### `EMAIL_HOST_PASSWORD`

Default: `''`

Password to use for the SMTP server.

#### `EMAIL_PORT`

Default: `25`

Port to use for the SMTP server.

#### `EMAIL_SUBJECT_PREFIX`

Default: `[Portfolio]`

Subject-line prefix for sent E-Mail messages.

#### `EMAIL_USE_LOCALTIME`

Default: `True`

Whether to send the SMTP Date header of E-Mail messages in the local time zone (`True`) or in UTC (`False`).

#### `EMAIL_USE_TLS`

Default: `False`

Whether to use a TLS (secure) connection when talking to the SMTP server.

### `FORCE_SCRIPT_NAME`

Default: `/portfolio`

In a production deployment with other base components, this base path should be set for Portfolio. Can stay empty in local standalone development.

### Geolocation Settings

The following settings are for geocoding locations/addresses.
By default GND is used to look up places. You can additionally use
the GeoNames database at geonames.org, if you provide your username for it.
Or you can instead use only the Pelias cloud service on geocode.earth or a
self-hosted Pelias service by providing your API key (and in the self-hosted
case the API url). For Pelias, you can also set a focus point from where to search.
Our recommendation is to use Pelias for highest accuracy. The `PELIAS_SOURCE_NAME`
is used to provide a label for the source.

#### `GEONAMES_USER`

Default: `None`

User for GeoNames database at geonames.org.

#### `PELIAS_API_KEY`

Default: `None`

API key for Pelias.

#### `PELIAS_API_URL`

Default: `https://api.geocode.earth/v1`

URL to Pelias API.

#### `PELIAS_FOCUS_POINT_LAT`

Default: `48.208126` (Latitude of Angewandte)

Focus point latitude.

#### `PELIAS_FOCUS_POINT_LON`

Default: `16.382464` (Longitude of Angewandte)

Focus point longitude.

#### `PELIAS_SOURCE_NAME`

Default: `geocode.earth`

Source name to display in the frontend and save in the database.

### `OPEN_API_VERSION`

Default: `2.0`

The version number of the generated Open API specification. You shouldn't change this.

### `SESSION_COOKIE_DOMAIN`

Default: `None`

The domain that should be used for the session cookies. Leave empty for a standard domain cookie.

See https://docs.djangoproject.com/en/2.2/ref/settings/#session-cookie-domain for further details.

### `SITE_URL`

The base URL of the Django site, e.g. for local development `http://localhost:8200/`

### `USER_QUOTA`

Default: `1073741824` (10 GB)

The disk quota a user has for their uploads (gets multiplied by the number of
years an account already exists (1 in the first year)).

### Showroom settings

The following settings are needed if you want to be able to sync entries
to a Showroom instance. This feature will only work if you set all of the
following settings.

#### `SYNC_TO_SHOWROOM`

Default: False

This setting determines, whether to sync published Portfolio entries to a
Showroom instance, that is configured by the following parameters.

#### `SHOWROOM_API_BASE`

Default: `None`

The base URL for the Showroom API that should be used to push entries to,
including a trailing slash. For a production server this might look something
like `http://showroom-django/api/v1/`, depending on your docker setup. For
a local dev environment it might rather be something like
`http://127.0.0.1:8500/api/v1/`.

#### `SHOWROOM_API_KEY`

Default: `None`

The API key for this Portfolio instance, as it is defined in the Showroom admin.

#### `SHOWROOM_REPO_ID`

Default: `None`

The repository ID for this Portfolio instance, as it is defined in the Showroom admin.
