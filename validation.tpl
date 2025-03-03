{{- define "validate.containers" -}}
  {{- /* Configurable parameters (could move to values.yaml) */ -}}
  {{- $allowedKinds := list "Deployment" "DaemonSet" "StatefulSet" -}}
  {{- $requiredContainerChecks := list "livenessProbe" "readinessProbe" "resources" -}}
  {{- $requiredInitContainerChecks := list "resources" -}} {{- /* Init containers often don't need probes */ -}}
  {{- $requireResourceLimits := true -}}

  {{- range $name, $workload := .Values -}}
    {{- if and (kindIs "map" $workload) (hasKey $workload "kind") (hasKey $workload "metadata") -}}
      {{- $workloadKind := get $workload "kind" -}}
      {{- $metadata := get $workload "metadata" | default dict -}}
      {{- $workloadName := get $metadata "name" | default (printf "unnamed-%s" $name) -}}

      {{- if has $workloadKind $allowedKinds -}}
        {{- $specPath := get (get $workload "spec" | default dict) "template" | default dict -}}
        {{- $podSpec := get $specPath "spec" | default dict -}}
        {{- $containers := get $podSpec "containers" | default list -}}
        {{- $initContainers := get $podSpec "initContainers" | default list -}}

        {{- /* ✅ Corrected Container existence check */ -}}
        {{- if and (eq (len $containers) 0) (eq (len $initContainers) 0) -}}
          {{- fail (printf "%s %s: Must have at least one container or initContainer" $workloadKind $workloadName) -}}
        {{- end -}}

        {{- /* Container validation */ -}}
        {{- range $containerType, $containers := dict "container" $containers "initContainer" $initContainers -}}
          {{- range $container := $containers -}}
            {{- $containerName := .name | default (printf "unnamed-%s" $containerType) -}}
            
            {{- /* Type-specific checks */ -}}
            {{- $checks := ternary $requiredContainerChecks $requiredInitContainerChecks (eq $containerType "container") -}}
            {{- range $check := $checks -}}
              {{- if not (hasKey . $check) -}}
                {{- fail (printf "%s %s: %s '%s' missing required '%s'" $workloadKind $workloadName $containerType $containerName $check) -}}
              {{- end -}}
            {{- end -}}

            {{- /* ✅ Enhanced resource validation */ -}}
            {{- if hasKey . "resources" -}}
              {{- $resources := .resources -}}
              {{- if not (hasKey $resources "requests") -}}
                {{- fail (printf "%s %s: %s '%s' missing resource requests" $workloadKind $workloadName $containerType $containerName) -}}
              {{- end -}}
              {{- if and $requireResourceLimits (not (hasKey $resources "limits")) -}}
                {{- fail (printf "%s %s: %s '%s' missing resource limits" $workloadKind $workloadName $containerType $containerName) -}}
              {{- end -}}
            {{- else -}}
              {{- fail (printf "%s %s: %s '%s' is missing a 'resources' section" $workloadKind $workloadName $containerType $containerName) -}}
            {{- end -}}

            {{- /* Security context warning */ -}}
            {{- if not (hasKey . "securityContext") -}}
              {{- warn (printf "%s %s: %s '%s' missing securityContext" $workloadKind $workloadName $containerType $containerName) -}}
            {{- end -}}
          {{- end -}}
        {{- end -}}
      {{- end -}}
    {{- end -}}
  {{- end -}}
{{- end -}}
