{{- define "validate.containers" -}}
  {{- $allowedKinds := list "Deployment" "StatefulSet" "DaemonSet" -}}

  {{- range $key, $workload := .Values }}
    {{- if and (kindIs "map" $workload) (hasKey $workload "kind") -}}
      {{- $workloadKind := get $workload "kind" | default "" }}
      {{- $metadata := get $workload "metadata" | default dict }}
      {{- $workloadName := get $metadata "name" | default $key }}  {{/* Prevent nil pointer errors */}}

      {{- if has $workloadKind $allowedKinds -}}
        {{- $spec := get $workload "spec" | default dict }}
        {{- $template := get $spec "template" | default dict }}
        {{- $podSpec := get $template "spec" | default dict }}
        {{- $containers := get $podSpec "containers" | default list }}

        {{- if eq (len $containers) 0 }}
          {{- fail (printf "Error: %s '%s' must have at least one container." $workloadKind $workloadName) }}
        {{- end }}

        {{- range $container := $containers }}
          {{- $containerName := get $container "name" | default "unnamed-container" }}

          {{- if not (hasKey $container "livenessProbe") }}
            {{- fail (printf "Error: %s '%s': Container '%s' is missing 'livenessProbe'." $workloadKind $workloadName $containerName) }}
          {{- end }}

          {{- if not (hasKey $container "readinessProbe") }}
            {{- fail (printf "Error: %s '%s': Container '%s' is missing 'readinessProbe'." $workloadKind $workloadName $containerName) }}
          {{- end }}

          {{- $resources := get $container "resources" | default dict }}
          {{- if not (hasKey $resources "requests") }}
            {{- fail (printf "Error: %s '%s': Container '%s' is missing 'resources.requests'." $workloadKind $workloadName $containerName) }}
          {{- end }}

          {{- if not (hasKey $resources "limits") }}
            {{- fail (printf "Error: %s '%s': Container '%s' is missing 'resources.limits'." $workloadKind $workloadName $containerName) }}
          {{- end }}
        {{- end }}
      {{- end }}
    {{- end }}
  {{- end }}
{{- end }}
