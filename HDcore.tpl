{{- define "validate.containers" -}}
  {{- $allowedKinds := list "Deployment" "StatefulSet" "DaemonSet" -}}

  {{- range $key, $workload := .Values }}
    {{- if and (kindIs "map" $workload) (hasKey $workload "kind") -}}
      {{- $workloadKind := get $workload "kind" }}
      {{- $workloadName := get (get $workload "metadata") "name" | default $key }}

      {{- if has $workloadKind $allowedKinds -}}
        {{- $podSpec := get (get $workload "spec") "template" | default dict | get "spec" | default dict }}
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
