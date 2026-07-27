# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog.

## [Unreleased]

## [0.2.0] - 2026-07-26

### Added

- Exported Grafana dashboards to JSON files in grafana/dashboards.
- Exported Grafana library elements to JSON files in grafana/library-elements.
- Exported Grafana playlists to JSON files in grafana/playlists.
- Exported Grafana alerting configuration to JSON files in grafana/alerting.
- Added datasource provisioning file in grafana/provisioning/datasources/datasources.yml.
- Added dashboard provisioning file in grafana/provisioning/dashboards/dashboards.yml.
- Added export automation script in scripts/export_grafana_state.py.
- Added secrets template file for Grafana in systemd/grafana-secrets.env.example.
- Added secrets template file for Node-RED in systemd/node-red-secrets.env.example.
- Added gitignore entries to prevent accidental database commits in .gitignore.

### Changed

- Updated grafana/conf/defaults.ini to read admin credentials and secret key from environment variables.
- Enabled domain enforcement in grafana/conf/defaults.ini.
- Updated systemd/grafana-server.service to support optional external secrets file.
- Updated node-red/settings.js to read admin username and password hash from environment variables.
- Updated node-red/settings.js to fail fast when required auth environment variables are missing.
- Updated systemd/node-red.service to support optional external secrets file.

### Security

- Removed hardcoded Grafana credentials and signing key from tracked configuration.
- Removed hardcoded Node-RED admin credentials from tracked configuration.
- Enforced secrets injection through environment at deploy time.
