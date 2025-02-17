{{- define "custom.labels" -}}
  {{- $globalLabels := .Values.global.labels | default dict -}}
  {{- $envLabels := .Values.labels | default dict -}}
  {{- $chartLabels := .Values.chartLabels | default dict -}}

  {{- $merged := dict -}}

  {{- if $globalLabels -}}
    {{- $merged = merge $merged $globalLabels -}}
  {{- end -}}

  {{- if $envLabels -}}
    {{- $merged = merge $merged $envLabels -}}
  {{- end -}}

  {{- if $chartLabels -}}
    {{- $merged = merge $merged $chartLabels -}}
  {{- end -}}

  {{- /* Convert merged dictionary to YAML then back to dictionary to ensure all values are strings */ -}}
  {{- $merged = $merged | toYaml | fromYaml -}}

  {{- $labelsYaml := toYaml $merged | nindent 4 -}}
  {{- tpl $labelsYaml . -}}
{{- end }}
