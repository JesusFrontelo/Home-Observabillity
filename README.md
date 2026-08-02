# Home-Observabillity

Stack de observabilidad domestico con Prometheus, Grafana, Alertmanager, Node-RED y varios exporters.

Nota: los cambios de seguridad y endurecimiento se documentan en CHANGE.md.

## Arquitectura y relaciones

```mermaid
flowchart LR
	%% Logos en nodos (Mermaid image shape)
	%% Componentes con logo local: Node-RED, Prometheus, Grafana, Gmail
	subgraph FIELD[Campo / Edge]
		IOT[Dispositivos IoT\nModbus TCP]
	end

	subgraph COLLECT[Captura y Export]
		NR@{ img: "docs/logos/nodered.svg", label: "Node-RED\nFlujos + /metricas", pos: "r", w: 48, h: 48 }
		MBX[modbus_exporter\nModbus -> Prometheus]
		NEX[node_exporter\nMétricas del host]
	end

	subgraph OBS[Core de Observabilidad]
		PROM@{ img: "docs/logos/prometheus.svg", label: "Prometheus\nScrape + Reglas", pos: "r", w: 48, h: 48 }
		GRAF@{ img: "docs/logos/grafana.svg", label: "Grafana\nDashboards + Alerting UI", pos: "r", w: 48, h: 48 }
		AM[Alertmanager\nRuteo de alertas]
	end

	subgraph NOTIF[Notificación]
		POSTFIX[Postfix local\nRelay SMTP]
		GMAIL@{ img: "docs/logos/gmail.svg", label: "Gmail SMTP\nSmarthost", pos: "r", w: 48, h: 48 }
		MAIL[Destinatarios\nEmail final]
	end

	subgraph CFG[GitOps / Config]
		REPO[Repositorio GitHub\nYAML + JSON + systemd]
	end

	IOT -->|Lectura Modbus| NR
	IOT -->|Lectura Modbus| MBX

	NR -->|/metricas| PROM
	MBX -->|/metrics| PROM
	NEX -->|/metrics| PROM

	PROM -->|Consultas PromQL| GRAF
	PROM -->|Alertas firing| AM

	AM -->|SMTP :25| POSTFIX
	POSTFIX -->|TLS 587| GMAIL
	GMAIL -->|Entrega| MAIL

	REPO -. despliega .-> PROM
	REPO -. despliega .-> GRAF
	REPO -. despliega .-> AM
	REPO -. despliega .-> NR
	REPO -. despliega .-> MBX

	classDef edge fill:#E6F7FF,stroke:#1D4ED8,stroke-width:1.4px,color:#0F172A
	classDef collect fill:#ECFDF5,stroke:#047857,stroke-width:1.4px,color:#052E16
	classDef core fill:#FFF7ED,stroke:#C2410C,stroke-width:1.4px,color:#431407
	classDef notif fill:#FEF2F2,stroke:#B91C1C,stroke-width:1.4px,color:#450A0A
	classDef cfg fill:#F5F3FF,stroke:#6D28D9,stroke-width:1.4px,color:#2E1065

	class IOT edge
	class NR,MBX,NEX collect
	class PROM,GRAF,AM core
	class POSTFIX,GMAIL,MAIL notif
	class REPO cfg
```

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

## Alertmanager por email con Postfix relay (Gmail)

Para que Alertmanager pueda enviar correos, se puede usar Postfix como relay SMTP local y Gmail como smarthost.

1. Instalar Postfix y dependencias SASL:

```bash
sudo apt update
sudo apt install -y postfix libsasl2-modules ca-certificates
```

2. Configurar `/etc/postfix/main.cf` con relay Gmail:

```conf
relayhost = [smtp.gmail.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_security_level = encrypt
smtp_tls_CAfile = /etc/ssl/certs/ca-certificates.crt
```

3. Crear credenciales de relay (usar App Password de Gmail):

```bash
echo "[smtp.gmail.com]:587 TU_USUARIO_GMAIL@gmail.com:TU_APP_PASSWORD" | sudo tee /etc/postfix/sasl_passwd > /dev/null
sudo postmap /etc/postfix/sasl_passwd
sudo chown root:root /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db
sudo chmod 600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db
sudo systemctl restart postfix
sudo systemctl enable postfix
```

4. Probar envío desde el host:

```bash
echo "test smtp relay" | mail -s "postfix relay test" destinatario@example.com
```

5. Alertmanager:

- El fichero `alertmanager/alertmanager.yml` ya incluye receptor `gmail-email` y salida SMTP por `127.0.0.1:25`.
- Ajustar `to:` con el destinatario real.
- Recargar/reiniciar Alertmanager tras cambios de configuración.
- Los valores sensibles deben inyectarse en despliegue (GitHub Environment Secrets) y escribirse en `/etc/default/*` en el host; no se versionan plantillas de secretos en este repositorio.

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
