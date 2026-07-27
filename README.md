# Home-Observabillity

Stack de observabilidad domestico con Prometheus, Grafana, Alertmanager, Node-RED y varios exporters.

Nota: los cambios de seguridad y endurecimiento se documentan en CHANGE.md.

## Versiones instaladas

Las siguientes versiones se han verificado directamente en el servidor remoto.

| Componente | Version |
| --- | --- |
| Prometheus | 2.54.1 |
| Grafana | 11.2.2 |
| Alertmanager | 0.27.0 |
| Node-RED | 4.0.5 |
| node_exporter | 1.8.2 |
| modbus_exporter | 0.4.1 |

## Módulos adicionales de Node-RED

Además de la instalación base de Node-RED, en el directorio de usuario (`/home/prometheus/.node-red`) están instalados estos módulos contrib:

| Módulo | Version |
| --- | --- |
| node-red-contrib-buffer-parser | 3.2.2 |
| node-red-contrib-modbus | 5.42.0 |
| node-red-contrib-modbus-tcp-ip | 1.1.5 |
| node-red-contrib-modbustcp | 1.2.3 |
| node-red-contrib-prometheus-exporter | 1.0.5 |
| node-red-contrib-re-modbus-tcp-ip | 1.2.0 |

## Notas para despliegue con GitHub Actions

- Mantener fijos los binarios y/o imágenes por versión para evitar cambios inesperados.
- Incluir en el pipeline la instalación de dependencias de Node-RED con `npm ci` dentro de `/home/prometheus/.node-red` (o en el userDir que uses en producción).
- Versionar y desplegar junto al proyecto los ficheros de configuración:
	- `/opt/prometheus/prometheus.yml`
	- `/opt/alertmanager/alertmanager.yml`
	- `/opt/modbus_exporter/modbus.yml`
	- Configuración y flujos de Node-RED (userDir)

## Grafana: dashboards JSON sin duplicados en despliegue

Se ha habilitado provisioning por archivos en:

- `grafana/provisioning/dashboards/dashboards.yml`

Configuración clave:

- Fuente de dashboards: `/opt/grafana/dashboards`
- Carpeta en Grafana: `Provisioned`
- `allowUiUpdates: false` para evitar deriva entre UI y Git
- `disableDeletion: false` para que eliminar un JSON en Git también lo elimine en Grafana

Para evitar duplicados:

- Mantener el campo `uid` en cada JSON (ya viene en los exportados).
- No duplicar un dashboard con distinto `uid` y mismo título.
- Si migras una instancia que ya tenía dashboards manuales, hacer una limpieza inicial de duplicados por título/uid antes del primer despliegue provisionado.

## Grafana: recursos extraídos desde la base de datos

Además de dashboards, se han exportado estos recursos para no depender de `grafana.db`:

- Datasource provisioning:
	- `grafana/provisioning/datasources/datasources.yml`
- Library Panels:
	- `grafana/library-elements/*.json`
- Playlists:
	- `grafana/playlists/*.json`
- Configuración de alertmanager de Grafana:
	- `grafana/alerting/*.json`

Regeneración automática (cuando cambie `grafana.db`):

- `./scripts/export_grafana_state.py`

## Orden recomendado de despliegue de Grafana

1. Configurar arranque de Grafana (`defaults.ini`, `systemd`).
2. Desplegar datasources por provisioning (`grafana/provisioning/datasources`).
3. Cargar Library Panels (desde `grafana/library-elements`) antes de dashboards que los usen.
4. Desplegar dashboards provisionados (`grafana/dashboards`).
5. Aplicar playlists y configuración de alerting si se usan.

Notas:

- El dashboard `Observability` (uid `swQF-UG4z`) usa Library Panels.
- Si no se cargan primero los Library Panels, ese dashboard puede aparecer incompleto o con errores.
