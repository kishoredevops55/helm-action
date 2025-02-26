{{/* Common Labels - Enforce Mandatory Labels */}}
{{- define "loki.labels" -}}

{{- $mandatoryLabels := .Values.mandatoryLabels | default list }}
{{- $userDefinedLabels := merge (dict) .Values.anchors.labels }}

{{/* Ensure Mandatory Labels Exist */}}
{{- range $mandatoryLabels }}
  {{- if not (hasKey $userDefinedLabels .) }}
    {{- fail (printf "❌ Missing mandatory label: %s" .) }}
  {{- end }}
{{- end }}

helm.sh/chart: {{ include "loki.chart" . }}

app.kubernetes.io/name: {{ .Chart.Name | toString }}

app.kubernetes.io/instance: {{ .Release.Name }}

{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}

app.kubernetes.io/managed-by: {{ .Release.Service }}

{{/* Add User-Defined Labels (only from anchors.labels) */}}
{{- range $key, $value := $userDefinedLabels }}
{{ $key }}: {{ $value | quote }}
{{- end }}

{{- end }}


{{/* Selector Labels */}}
{{- define "loki.selectorLabels" -}}

app.kubernetes.io/name: {{ .Chart.Name | toString }}

app.kubernetes.io/instance: {{ .Release.Name }}

{{- range $key, $value := .Values.anchors.labels }}
{{ $key }}: {{ $value | quote }}
{{- end }}

{{- end }}

mandatoryLabels:
  - app
  - appname
  - portfolio
  - dr_category

anchors:
  labels:
    app: my-app
    appname: loki-service
    portfolio: logging
    dr_category: tier-1
    environment: production

