# Home-Observabillity

Stack de observabilidad domestico con Prometheus, Grafana, Alertmanager, Node-RED y varios exporters.

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
