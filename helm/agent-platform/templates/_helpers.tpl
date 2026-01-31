{{/*
Expand the name of the chart.
*/}}
{{- define "agent-platform.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "agent-platform.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "agent-platform.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "agent-platform.labels" -}}
helm.sh/chart: {{ include "agent-platform.chart" . }}
{{ include "agent-platform.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "agent-platform.selectorLabels" -}}
app.kubernetes.io/name: {{ include "agent-platform.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "agent-platform.serviceAccountName" -}}
{{- if .Values.security.serviceAccount.create }}
{{- default (include "agent-platform.fullname" .) .Values.security.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.security.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Get the image registry
*/}}
{{- define "agent-platform.imageRegistry" -}}
{{- .Values.global.imageRegistry | default "ghcr.io" }}
{{- end }}

{{/*
Common environment variables for all services
*/}}
{{- define "agent-platform.commonEnv" -}}
- name: ENVIRONMENT
  value: {{ .Values.global.environment | quote }}
- name: LOG_LEVEL
  value: {{ .Values.config.api.logLevel | quote }}
- name: POSTGRES_HOST
  value: "postgres"
- name: POSTGRES_PORT
  value: "5432"
- name: POSTGRES_DB
  value: {{ .Values.postgresql.auth.database | quote }}
- name: POSTGRES_USER
  value: {{ .Values.postgresql.auth.username | quote }}
- name: POSTGRES_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Values.postgresql.auth.existingSecret | default "platform-secrets" }}
      key: {{ .Values.postgresql.auth.secretKeys.adminPasswordKey }}
- name: REDIS_HOST
  value: "redis"
- name: REDIS_PORT
  value: "6379"
- name: RABBITMQ_HOST
  value: "rabbitmq"
- name: RABBITMQ_PORT
  value: "5672"
- name: RABBITMQ_USER
  value: {{ .Values.rabbitmq.auth.username | quote }}
- name: RABBITMQ_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ .Values.rabbitmq.auth.existingSecret | default "platform-secrets" }}
      key: {{ .Values.rabbitmq.auth.secretKeys.passwordKey }}
{{- end }}

{{/*
API Keys environment variables
*/}}
{{- define "agent-platform.apiKeysEnv" -}}
- name: ANTHROPIC_API_KEY
  valueFrom:
    secretKeyRef:
      name: platform-secrets
      key: anthropic-api-key
      optional: true
- name: OPENAI_API_KEY
  valueFrom:
    secretKeyRef:
      name: platform-secrets
      key: openai-api-key
      optional: true
- name: GOOGLE_API_KEY
  valueFrom:
    secretKeyRef:
      name: platform-secrets
      key: google-api-key
      optional: true
{{- end }}
