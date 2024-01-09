# Changelog

## 1.3.5

## Changed

- move healtcheck to docker-compose.yml
- set start_period and interval for healthchecks
- update documentation

## 1.3.4

### Added

- configurable error handling for push_to_showroom
- add HealthCheckMiddleware
- make RQ result TTL configurable
- make Redis port configurable
- add documentation for `REDIS_PORT` and `RQ_RESULT_TTL`
- add documentation for Showroom sync

### Changed

- **BREAKING**: change default value of CAS_SERVER_URL to `f'{SITE_URL}auth/'`
- use general config from https://github.com/base-angewandte/config
- improve docker configuration with healthchecks and `depends_on`
- update documentation style and environment
- upgrade middleware to new django style
- upgrade python to 3.8
- upgrade django to 3.2
- update requirements

### Fixed

- fix pip-sync in docker dev setup
- change styling of … in invalid json highlighting
- add migrations for jsonfield changes
- fix cors settings
- fix python version for readthedocs
- only push entry if still published at worker runtime

# 1.3.3

### Added

- add readthedocs configuration

### Fixed

- **clamav**: catch BufferTooLongError

## 1.3.2

### Added

- Added timeout to Pelias configuration
- Added `PELIAS_API_KEY_LOCATION` configuration
- Added possibility to export all published entries

### Changed

- Updated pre-commit configuration

## 1.3.1

## Added

- Added `all` parameter to `/api/v1/user/{id}/data/` to be able to also return entries in which the user isn't a contributor

### Changed

- **BREAKING**: Updated pre-commit configuration to also enforce the use of conventional commit messages
- **BREAKING**: Changed redirect response from 301 to 308
- **BREAKING**: Default value for `data` is now an empty dict
- Install exiftool via github instead of sourceforge in docker image

## 1.3

### Added

- Added autosuggest route for Primo API
- Added `CAS_CHECK_NEXT` environment variable for development and documentation for it
- Added `first_name` and `last_name` to API user response
- Added ClamAV and scan uploaded media objects
- Added bulk creation of entries for importer
- Added project mapping in skosmos.py
- Added `get_preflabel_via_uri` in skosmos.py
- Added management command to update all labels
- Added management commands to evaluate keywords usage of published entries

### Changed

- **BREAKING**: Update all labels on every update of Portfolio
- **BREAKING**: Adapted API user response to use `request.user.get_full_name()` instead of the CAS attribute `display_name` to be consistent over multiple Portfolio instances
- Updated pre-commit configuration

### Fixed

- Fixed `fix_keywords` management command

## 1.2.1

### Fixed

- Fixed CC licenses label in API

## 1.2

### Added

- Send 301 for retrieve requests in EntryViewSet with old entry ids
- Added Showroom connector
- Added connection to User Preferences API
- Added support for Sentry
- Added possibility to sort media objects
- Added possibility to feature a media object
- Added showroom_id field to Entry model
- Added support for nginx crop and resize in media_server
- Added crop and resize to dev config of nginx
- Added management command to push entries to Showroom
- Added management command to manually start the conversion process of a media object
- Added management command to fix missing previews
- Added management commands for fixing migrations issues
- Added documentation of Showroom settings

### Changed

- **BREAKING**: Updated shortuuid to 1.0.8
- **BREAKING**: Migrated all existing shortuuids to new format
- **BREAKING**: Migrated all existing media directories
- Changed search from TrigramSimilarity to TrigramWordSimilarity
- Increased max_length of FileField in Media model
- Adapted dev config of nginx

### Fixed

- Fixed prefLabel caching in skosmos.py

## 1.1.6

### Changed

- New API lists logic

### Fixed

- Corrected lang parameter for type label in `export_published` management command

## 1.1.5

### Added

- **EXPERIMENTAL**: Added `import_bibtex` management command for importing entries from BibTeX files

## 1.1.4

### Fixed

- Fixed build error due to exiftool.org being down - thanks to Benjamin Höglinger-Stelzer [nefarius]

## 1.1.3

### Changed

- Optimized docker-compose builds

### Fixed

- Fixed error during preview creation of documents containing umlauts

## 1.1.2

### Added

- Added status field to ResearchProjectSchema

### Changed

- New API lists logic
- Pull docker images before build
- Updated pre-commit and hooks
- Clean up docs container after running
- Returning additional metadata for media that hasn't been converted yet
- Changed license to required for media objects

### Fixed

- Changed container name in `docker-compose.override.dev-docker.yml` to `portfolio-django`

## 1.1.1

### Added

- Added support for new INDEX vocabulary collections

## 1.1.0

### Added

- Changelog beginning with this version
- Added sphinx documentation and possibility to build it via docker (`make build-docs`) and serve it via django
- Added additional configuration possibilities via environment variables, see documentation for details
- Added possbility to set imagemagick policy and added two example configurations
- gunicorn port is configurable via `GUNICORN_PORT` environment variable
- gunicorn workers are configurable via `GUNICORN_WORKERS` environment variable
- Added possibility to use docker during development
- Added `pip-compile-upgrade` to Makefile
- Added layers setting to Pelias
- Using pyupgrade, black, double-quote-string-fixer, end-of-file-fixer, docformatter, flake8-bugbear, pep8-naming,
  bandit, docker-compose-check and hadolint with pre-commit
- Added possibility to get detailed results from `/api/v1/entry/{id}/media/` and adapted `get_media_for_entry`
  accordingly
- Added `/api/v1/entry/{id}/data` to API
- Added `date_created` to relations in API
- Added images for parent entries in API results
- Added creation date of relations in API results
- Added ParentSerializer
- Added `parents` to EntrySerializer
- Added media and relations to result of `/api/v1/user/{id}/data/{entry_id}/` and `/api/v1/entry/{id}/data/`
- Added possibility to send types as comma-separated values in `/api/v1/wbdata/`
- Added design and fellowship_visiting_affiliation schemas
- Added "project partnership" role to research project
- Added date range location group field
- Added possibility to set label for date time field
- Added default ordering by creation date for `Media` model
- Added keywords to search
- Added download parameter for media assets
- Published media assets can be accessed without login
- Added `get_active_schemas` function
- Raise `ValidationError` if type can't be matched to any schema
- Added `export_published` management command to export published entries as CSV
- Stop and delete `media_info_and_convert` jobs if media asset is deleted

### Changed

- **BREAKING**: CORS variables have been renamed:
  - `CORS_ORIGIN_WHITELIST` -> `CORS_ALLOWED_ORIGINS`
  - `CORS_ORIGIN_ALLOW_ALL` -> `CORS_ALLOW_ALL_ORIGINS`
- **BREAKING**: Updated vcrpy – your cassettes may need to be re-recorded if you have run tests before
- Updated requirements
- Updated collabora/code
- Updated docker-compose files to version 2.3
- Adapted pip configuration in Dockerfile
- Adapted flake8 configuration
- Changed from seed-isort-config to isort
- Use a configuration file for gunicorn
- exiftool is installed from source instead of from package
- Reduced `failure_ttl` of rq jobs from 1 year to approx. 3 months
- Changed event icon
- Changed ExifField to JSONField
- Changed ugettext_lazy to gettext_lazy
- Complete rewrite of `user_data` and adapted logic
- Better caching in `skosmos.py`
- Improved thumbnail creation for videos
- Improved video conversion

### Removed

- Removed ExifField

### Fixed

- Added missing label to "award ceremony" and "funding category"
- Added fallback for missing role label
- Correct some mime types
- Fixed handling of Photoshop files
- Fixed error during creation of thumbnail for pdfs
- Update requirements for rq containers on `make update`
