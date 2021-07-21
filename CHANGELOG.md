# Changelog

## unreleased

### Changed
- Pull docker images before build
- Updated pre-commit and hooks
- Clean up docs container after running

### Fixed
- Changed container name in `docker-compose.override.dev-docker.yml` to `portfolio-django`

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
