# Docker Overrides Configuration

This repository contains multiple docker-compose override files to demonstrate certain configuration possibilities.

## `docker-compose.override.dev.nginx.yml`

Use this override configuration if you want to run a setup with nginx locally.

## `docker-compose.override.dev.yml`

Use this override configuration for local development, because otherwise the ports of the required services are not
accessible locally.

## `docker-compose.override.dev-docker.yml`

Use this override configuration for local development via docker.

## `docker-compose.override.imagemagick.yml`

Use this override configuration for adapting the imagemagick policy xml.

In `docker/imagemagick/` you'll find two example policies. `policy.xml` which is the default used file and
`policy-high.xml` which is recommended if you expect to process large image files.
