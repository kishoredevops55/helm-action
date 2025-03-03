{{/*
Validate containers for readinessProbe, livenessProbe, and resource requests/limits.
1. Checks all containers for:
   a. Mandatory `readinessProbe`.
   b. Mandatory `livenessProbe`.
   c. Mandatory `resources.requests` and `resources.limits`.
2. Fails during Helm rendering if validation fails.

Parameters:
- $containers: an array of containers to validate.
- $kind: the resource kind (e.g., StatefulSet, Deployment) for error messages.
- $resourceName: the name of the resource being validated.

Usage:
{{ include "common.validateContainers" list .spec.template.spec.containers "StatefulSet" .metadata.name }}
*/}}
{{- define "common.validateContainers" -}}
{{- $containers := index . 0 -}}
{{- $kind := index . 1 | default "unknown-kind" -}}
{{- $resourceName := index . 2 | default "unknown-resource" -}}

{{- range $index, $container := $containers -}}

  {{- if not $container.readinessProbe }}
    {{- fail (printf "%s '%s': Container '%s' is missing a readinessProbe." $kind $resourceName $container.name) }}
  {{- end -}}

  {{- if not $container.livenessProbe }}
    {{- fail (printf "%s '%s': Container '%s' is missing a livenessProbe." $kind $resourceName $container.name) }}
  {{- end -}}

  {{- if or (not $container.resources.requests) (not $container.resources.limits) }}
    {{- fail (printf "%s '%s': Container '%s' is missing resource requests/limits (both required)." $kind $resourceName $container.name) }}
  {{- end -}}

{{- end -}}
{{- end -}}

{{/*
Validate init containers (using the same logic as standard containers).
This function is a wrapper for `common.validateContainers` and is modular so that you can validate init containers separately.
*/}}
{{- define "common.validateInitContainers" -}}
{{ include "common.validateContainers" . }}
  {{- end -}}

apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: {{ .Release.Name }}-statefulset
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Values.app }}
  template:
    metadata:
      labels:
        app: {{ .Values.app }}
    spec:
      containers:
        - name: {{ .Values.container.name }}
          image: {{ .Values.container.image }}
          readinessProbe:
            httpGet:
              path: /
              port: 8080
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
          resources:
            limits:
              cpu: "500m"
              memory: "128Mi"
            requests:
              cpu: "250m"
              memory: "64Mi"

      initContainers:
        - name: {{ .Values.initContainer.name }}
          image: {{ .Values.initContainer.image }}
          readinessProbe:
            httpGet:
              path: /init-ready
              port: 8080
          livenessProbe:
            httpGet:
              path: /init-healthz
              port: 8080
          resources:
            limits:
              cpu: "300m"
              memory: "64Mi"
            requests:
              cpu: "200m"
              memory: "32Mi"

# Add validation logic here for both containers and initContainers
{{- if .Values.validation.enabled }}
{{ include "common.validateContainers" list .spec.template.spec.containers "StatefulSet" .metadata.name }}
{{ include "common.validateInitContainers" list .spec.template.spec.initContainers "StatefulSet" .metadata.name }}
{{- end }



 apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-deployment
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Values.app }}
  template:
    metadata:
      labels:
        app: {{ .Values.app }}
    spec:
      containers:
        - name: {{ .Values.container.name }}
          image: {{ .Values.container.image }}
          readinessProbe:
            httpGet:
              path: /
              port: 8080
          livenessProbe:
            httpGet:
              path: /healthz
              port: 8080
          resources:
            limits:
              cpu: "500m"
              memory: "128Mi"
            requests:
              cpu: "250m"
              memory: "64Mi"

      initContainers:
        - name: {{ .Values.initContainer.name }}
          image: {{ .Values.initContainer.image }}
          readinessProbe:
            httpGet:
              path: /init-ready
              port: 8080
          livenessProbe:
            httpGet:
              path: /init-healthz
              port: 8080
          resources:
            limits:
              cpu: "300m"
              memory: "64Mi"
            requests:
              cpu: "200m"
              memory: "32Mi"

# Add validation logic here for both containers and initContainers
{{- if .Values.validation.enabled }}
{{ include "common.validateContainers" list .spec.template.spec.containers "Deployment" .metadata.name }}
{{ include "common.validateInitContainers" list .spec.template.spec.initContainers "Deployment" .metadata.name }}
{{- end }}


  # Enable or disable container validation
validation:
  enabled: true

# Sample StatefulSet and Deployment configuration
replicaCount: 3
app: my-app

container:
  name: app-container
  image: nginx:1.19

initContainer:
  name: init-container
  image: nginx:1.19
