{{- define "chart.environment" -}}
{{- $namespace := .Values.anchors.namespace | default "default-namespace" -}}
{{- $env := regexFind "[^-]+$" $namespace -}}
{{- $env | lower -}}  # Optional: convert to lowercase
{{- end -}}


{{/*
Generate application and standard labels, ensuring appcode is used consistently.
*/}}

{{- define "chart.labels" -}}
app: {{ include "chart.name" . }}-eh

app.kubernetes.io/instance: {{ include "chart.name" . }}

app.kubernetes.io/managed-by: Helm

app.kubernetes.io/name: {{ include "chart.appcode" . | lower }}

app.kubernetes.io/version: "1.16.0"

{{- with .Values.anchors.labels }}
{{- if .appcode }}
appcode: {{ .appcode | quote }}
{{- end }}

appname: {{ include "chart.name" . }}-eh

{{- if .costcenter }}
costcenter: {{ .costcenter | quote }}
{{- end }}

{{- if .drcategory }}
drcategory: {{ .drcategory | quote }}
{{- end }}

{{- if .environment }}
environment: {{ .environment | default (include "chart.environment" .) | quote }}
{{- else }}
environment: {{ include "chart.environment" . | quote }}
{{- end }}

{{- if (index . "helm.sh/chart") }}
helm.sh/chart: {{ (index . "helm.sh/chart") | quote }}
{{- end }}

{{- if .portfolio }}
portfolio: {{ .portfolio | quote }}
{{- end }}

{{- if .project }}
project: {{ .project | quote }}
{{- end }}

{{- range $key, $value := . }}
{{- if not (hasKey (list "appcode" "costcenter" "drcategory" "environment" "helm.sh/chart" "portfolio" "project") $key) }}
{{ $key }}: {{ $value | quote }}
{{- end }}
{{- end }}

{{- end }}
{{- end }}
