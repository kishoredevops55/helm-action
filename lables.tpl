{{/* Common Labels - Validate Only Where Used */}}
{{- define "loki.labels" -}}

{{- $mandatoryLabels := .Values.mandatoryLabels | default list }}
{{- $userDefinedLabels := .Values.anchors.labels | default dict }}

{{- $labels := dict }}

{{/* Validate Mandatory Labels, but only in used templates */}}
{{- if (include "loki.isLabelsUsed" .) }}
  {{- range $mandatoryLabels }}
    {{- if not (hasKey $userDefinedLabels .) }}
      {{- fail (printf "❌ Missing mandatory label: %s" .) }}
    {{- end }}
  {{- end }}
{{- end }}

{{/* Add Fixed Labels */}}
{{- $_ := set $labels "helm.sh/chart" (include "loki.chart" .) }}
{{- $_ := set $labels "app.kubernetes.io/name" .Chart.Name }}
{{- $_ := set $labels "app.kubernetes.io/instance" .Release.Name }}

{{- if .Chart.AppVersion }}
  {{- $_ := set $labels "app.kubernetes.io/version" (.Chart.AppVersion | quote) }}
{{- end }}

{{- $_ := set $labels "app.kubernetes.io/managed-by" .Release.Service }}

{{/* Add User-Defined Labels */}}
{{- range $key, $value := $userDefinedLabels }}
  {{- $_ := set $labels $key ($value | quote) }}
{{- end }}

{{/* Render Labels (No Extra Lines) */}}
labels:
{{- range $key, $value := $labels }}
  {{ $key }}: {{ $value }}
{{- end }}

{{- end }}


{{/* Check If Labels Are Used in This Template */}}
{{- define "loki.isLabelsUsed" -}}
  {{- $usedTemplates := list "deployment.yaml" "service.yaml" "statefulset.yaml" }}
  {{- if has .Template.Name $usedTemplates }}
    true
  {{- else }}
    false
  {{- end }}
{{- end }}


{{/* Check If Labels Are Used in This Template */}}
{{- define "loki.isLabelsUsed" -}}
  {{- $usedTemplates := list "deployment.yaml" "service.yaml" "statefulset.yaml" }}
  {{- if has .Template.Name $usedTemplates }}
    true
  {{- else }}
    false
  {{- end }}
{{- end }}

{{/* Selector Labels - No Extra Lines */}}
{{- define "loki.selectorLabels" -}}

app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}

{{- range $key, $value := .Values.anchors.labels }}
  {{ $key }}: {{ $value | quote }}
{{- end }}

{{- end }}

