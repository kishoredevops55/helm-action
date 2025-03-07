{{- define "validate.containers" -}}
  {{- $allowedKinds := list "Deployment" "StatefulSet" "DaemonSet" -}}

  {{- range $kind := $allowedKinds -}}
    {{- range $workload := (lookup "apps/v1" $kind .Release.Namespace "").items | default list -}}
      {{- $workloadName := get $workload.metadata "name" -}}
      {{- $podSpec := get $workload.spec.template.spec "containers" | default list -}}
      {{- $initContainers := get $workload.spec.template.spec "initContainers" | default list -}}

      {{- if or (eq (len $podSpec) 0) (eq (len $initContainers) 0) -}}
        {{- fail (printf "%s %s: Must have at least one container or initContainer" $kind $workloadName) -}}
      {{- end -}}

      {{- range concat $podSpec $initContainers -}}
        {{- $containerName := .name | default "unnamed-container" -}}

        {{- if not (hasKey . "livenessProbe") -}}
          {{- fail (printf "%s %s: Container '%s' is missing 'livenessProbe'" $kind $workloadName $containerName) -}}
        {{- end -}}

        {{- if not (hasKey . "readinessProbe") -}}
          {{- fail (printf "%s %s: Container '%s' is missing 'readinessProbe'" $kind $workloadName $containerName) -}}
        {{- end -}}

        {{- if not (hasKey . "resources") -}}
          {{- fail (printf "%s %s: Container '%s' is missing 'resources' section" $kind $workloadName $containerName) -}}
        {{- else -}}
          {{- $resources := .resources -}}
          {{- if not (hasKey $resources "requests") -}}
            {{- fail (printf "%s %s: Container '%s' is missing 'resources.requests'" $kind $workloadName $containerName) -}}
          {{- end -}}
          {{- if not (hasKey $resources "limits") -}}
            {{- fail (printf "%s %s: Container '%s' is missing 'resources.limits'" $kind $workloadName $containerName) -}}
          {{- end -}}
        {{- end -}}

      {{- end -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
