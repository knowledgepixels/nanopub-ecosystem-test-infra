{{/*
Expand the name of the chart.
*/}}
{{- define "query.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "query.fullname" -}}
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
{{- define "query.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "query.labels" -}}
helm.sh/chart: {{ include "query.chart" . }}
{{ include "query.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "query.selectorLabels" -}}
app.kubernetes.io/name: {{ include "query.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "query.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "query.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Name of the component application.
*/}}
{{- define "application.name" -}}
{{- printf "%s-application" (include "query.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified component application name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "application.fullname" -}}
{{- printf "%s-application" (include "query.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Component application labels
*/}}
{{- define "application.labels" -}}
helm.sh/chart: {{ include "query.chart" . }}
{{ include "application.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Component application selector labels
*/}}
{{- define "application.selectorLabels" -}}
app.kubernetes.io/name: {{ include "query.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: application
isMainInterface: "yes"
tier: {{ .Values.application.tier }}
{{- end }}

{{/*
Name of the component rdf4j.
*/}}
{{- define "rdf4j.name" -}}
{{- printf "%s-rdf4j" (include "query.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified component rdf4j name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "rdf4j.fullname" -}}
{{- printf "%s-rdf4j" (include "query.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create the default FQDN for rdf4j headless service.
*/}}
{{- define "rdf4j.svc.headless" -}}
{{- printf "%s-headless" (include "rdf4j.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Component rdf4j labels
*/}}
{{- define "rdf4j.labels" -}}
helm.sh/chart: {{ include "query.chart" . }}
{{ include "rdf4j.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Component rdf4j selector labels
*/}}
{{- define "rdf4j.selectorLabels" -}}
app.kubernetes.io/name: {{ include "query.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
query: {{ .Chart.Name }}
app.kubernetes.io/component: rdf4j
isMainInterface: "no"
tier: {{ .Values.rdf4j.tier }}
{{- end }}

{{/*
Name of the component grlc.
*/}}
{{- define "grlc.name" -}}
{{- printf "%s-grlc" (include "query.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified component grlc name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "grlc.fullname" -}}
{{- printf "%s-grlc" (include "query.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}


{{/*
Component grlc labels
*/}}
{{- define "grlc.labels" -}}
helm.sh/chart: {{ include "query.chart" . }}
{{ include "grlc.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Component grlc selector labels
*/}}
{{- define "grlc.selectorLabels" -}}
app.kubernetes.io/name: {{ include "query.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
query: {{ .Chart.Name }}
app.kubernetes.io/component: grlc
isMainInterface: "yes"
tier: {{ .Values.grlc.tier }}
{{- end }}
