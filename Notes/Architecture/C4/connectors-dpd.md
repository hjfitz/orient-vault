---
tags: [c4, architecture, c4-component]
service: connectors-dpd
level: component
source_repo: /home/hjf/code/apiky-survey/ado/connectors-dpd
source_sha: fad40eb7e7c09a9cbece1e0cdb773c9ff92c8787
generated: 2026-11-09
confidence: medium
confidence_reason: "Every in-repo component was read in source; the framework internals were read in a sibling checkout (tracking-core c081108, same 0.6.2 version), and prod config (which DPD API version runs) could not be seen."
---
# connectors-dpd: C4 components

connectors-dpd is a .NET polling connector for DPD and DPD Local (one image, two configs). It pulls due parcels from batch-creator over gRPC, asks DPD about each, and streams results to response-publisher.

```orient-flow
{
  "v": 1,
  "preset": "c4-component",
  "title": "Component diagram: connectors-dpd (not shown: Datadog logs and metrics, topics downstream of response-publisher)",
  "groups": [
    { "id": "dpd", "label": "connectors-dpd (.NET connector)" }
  ],
  "nodes": [
    { "id": "worker", "label": "Batch worker", "kind": "step", "tech": "Connector framework 0.6.2", "sub": "Pulls a batch, runs requests in parallel", "group": "dpd" },
    { "id": "rh", "label": "Tracking request handler", "kind": "step", "tech": "Connector framework 0.6.2", "sub": "Maps provider exceptions to error reasons", "group": "dpd" },
    { "id": "streamer", "label": "Response streamer", "kind": "step", "tech": "Connector framework 0.6.2", "sub": "Streams each result back", "group": "dpd" },
    { "id": "provider", "label": "DPDTrackingProvider", "kind": "step", "tech": "C# ITrackingProvider", "sub": "Passes parcel and contract to the DPD client", "group": "dpd" },
    { "id": "xml", "label": "DPD XML client", "kind": "step", "tech": "C# HttpClient, XmlSerializer", "sub": "Default client; handles relabels and DPD Local retry", "group": "dpd" },
    { "id": "json", "label": "DPD JSON client", "kind": "step", "tech": "C# HttpClient, Newtonsoft", "sub": "Used only if System:DPDApiVersion is json", "group": "dpd" },
    { "id": "xmlmap", "label": "XML response mapper", "kind": "step", "tech": "C#", "sub": "DPD XML to Tracking events", "group": "dpd" },
    { "id": "jsonmap", "label": "JSON response mapper", "kind": "step", "tech": "C#", "sub": "DPD JSON to Tracking events", "group": "dpd" },
    { "id": "creds", "label": "Carrier credentials provider", "kind": "step", "tech": "C# HttpClient", "sub": "Fetches per-contract DPD login", "group": "dpd" },
    { "id": "repo", "label": "Parcel repository", "kind": "step", "tech": "MongoDB.Driver", "sub": "Parcel number to latest tracking number", "group": "dpd" },
    { "id": "host", "label": "Host and config loader", "kind": "step", "tech": "Program.cs, SimpleInjector", "sub": "Wires components; --init mode", "group": "dpd" },
    { "id": "health", "label": "Health endpoints", "kind": "step", "tech": "Kestrel", "sub": "/healthz and /readyz, always Healthy", "group": "dpd" },

    { "id": "bc", "label": "batch-creator", "kind": "service", "tech": "tracking-core, gRPC", "sub": "Serves batches of due parcels" },
    { "id": "rp", "label": "response-publisher", "kind": "service", "tech": "tracking-core, gRPC", "sub": "Receives tracking responses" },
    { "id": "dpdapi", "label": "DPD tracking API", "kind": "external", "tech": "HTTP, XML or JSON", "sub": "Endpoint set by config" },
    { "id": "ccm", "label": "carrier-credentials-manager", "kind": "service", "tech": "HTTP API", "sub": "Serves per-contract carrier credentials" },
    { "id": "mongo", "label": "Parcel collection", "kind": "store", "tech": "MongoDB", "sub": "Database and collection set by config" },
    { "id": "etcd", "label": "Connector config", "kind": "store", "tech": "etcd", "sub": "Batch options and mapper settings" },
    { "id": "kube", "label": "Kubernetes probes", "kind": "external", "tech": "HTTP", "sub": "Not confirmed: no manifest in this repo", "unconfirmed": true }
  ],
  "edges": [
    { "from": "worker", "to": "bc", "label": "GetBatch (gRPC stream)" },
    { "from": "worker", "to": "rh", "label": "each tracking request" },
    { "from": "worker", "to": "streamer", "label": "stream of responses" },
    { "from": "streamer", "to": "rp", "label": "SendResponse (gRPC stream)" },
    { "from": "rh", "to": "provider", "label": "TrackParcel" },
    { "from": "provider", "to": "xml", "label": "Track (default)" },
    { "from": "provider", "to": "json", "label": "Track (if DPDApiVersion=json)" },
    { "from": "xml", "to": "creds", "label": "get credentials by contract" },
    { "from": "creds", "to": "ccm", "label": "GET credentials (HTTP)" },
    { "from": "xml", "to": "dpdapi", "label": "POST XML request" },
    { "from": "json", "to": "dpdapi", "label": "POST JSON, apikey header", "unconfirmed": true },
    { "from": "xml", "to": "repo", "label": "get / upsert latest number" },
    { "from": "json", "to": "repo", "label": "get / upsert latest number" },
    { "from": "xml", "to": "xmlmap", "label": "map response" },
    { "from": "json", "to": "jsonmap", "label": "map response" },
    { "from": "repo", "to": "mongo", "label": "find / upsert parcel" },
    { "from": "host", "to": "etcd", "label": "load and watch config" },
    { "from": "host", "to": "repo", "label": "--init: create unique index" },
    { "from": "kube", "to": "health", "label": "GET /healthz, /readyz", "unconfirmed": true }
  ]
}
```

## Elements

| id | name | kind | tech | responsibility | source |
| --- | --- | --- | --- | --- | --- |
| worker | Batch worker | step | Connector framework 0.6.2 (NuGet) | Hosted service. Per enabled batch option, calls batch-creator `GetBatch` and processes the stream in parallel | tracking-core `src/Gfs.Fenghuang.Tracking.Core.Frameworks.Connector/Tracking/Batch/CarrierConnectorWorker.cs:77`, `BatchRequestHandler.cs:37-48` |
| rh | Tracking request handler | step | Connector framework 0.6.2 | Calls the provider; turns credential, API, not-found and other exceptions into `ErrorReason` responses | tracking-core `.../Tracking/TrackingRequestHandler.cs:37-45`, catch blocks from `:58` |
| streamer | Response streamer | step | Connector framework 0.6.2 | Opens `SendResponse` and writes each response to the stream | tracking-core `.../Tracking/TrackingResponseStreamer.cs:43-62` |
| provider | DPDTrackingProvider | step | C# | Implements `ITrackingProvider`; delegates to `IDPDClient.Track(parcelNumber, contractNo)` | `src/Gfs.Fenghuang.Connectors.DPD.Core/DPDTrackingProvider.cs:21` |
| xml | DPD XML client | step | C# | Gets credentials, optionally swaps in the latest tracking number, POSTs `text/xml`, turns `USERNAME INVALID` / `PASSWORD INVALID` into credential errors, other errors into carrier or not-found errors. Upserts relabelled numbers. For connector name `dpdlocal` it retries once with the first 4 characters stripped | `src/Gfs.Fenghuang.Connectors.DPD.Core/XML/DPDClient.cs:50-152` (retry `:119`, relabel `:130-144`) |
| json | DPD JSON client | step | C# | POSTs JSON with an `apikey` header from settings; same latest-number lookup and relabel upsert. No carrier-credentials call | `.../JSON/DPDClient.cs:47-116`; selected at `src/Gfs.Fenghuang.Connectors.DPD/Program.cs:171-176` |
| xmlmap | XML response mapper | step | C# | Maps events, signatory (prefix/suffix trimming driven by `TrackingMapperSettings`), ETA window, raw response | `.../XML/DPDXmlTrackingResponseMapper.cs:22` |
| jsonmap | JSON response mapper | step | C# | Same job for the JSON shape | `.../JSON/DPDJsonTrackingResponseMapper.cs:26` |
| creds | Carrier credentials provider | step | C# HttpClient | `GET {EndPoint}/{contractNumber}`; 404 becomes a retriable `ContractCredentialsNotFoundException` | `.../Security/CarrierCredentialsProvider.cs:231-257` |
| repo | Parcel repository | step | MongoDB.Driver | `Get` and `Upsert` by parcel number; `SetupDatabase` creates unique index `parcelnumber_v1` | `.../DataAccess/ParcelRepository.cs:26,35,49` |
| host | Host and config loader | step | Program.cs, SimpleInjector | Builds config (appsettings, env, etcd with reload); registers the client chosen by `DPDApiVersion`; with `--init` or `INIT=true` runs `SetupDatabase` and exits | `src/Gfs.Fenghuang.Connectors.DPD/Program.cs:42-52,54-92,94-133,166-196` |
| health | Health endpoints | step | Kestrel | Separate web host on `Health:ListenPort`; `/healthz` and `/readyz` both return Healthy (ready check is a TODO) | `.../HealthChecks/HealthCheckHostedService.cs:17-42`, `ServiceReadyCheck.cs:83` |
| bc | batch-creator | service | tracking-core, gRPC | Serves `TrackingBatchServiceV1.GetBatch` | Endpoint from `System:TrackingBatchEndpoint` (`Program.cs:192`); `e2e/docker-compose.yaml` runs it as `System__Mode: BATCH_CREATOR` |
| rp | response-publisher | service | tracking-core, gRPC | Receives `ConnectorResponseServiceV1.SendResponse` | `Program.cs:193`; `e2e/docker-compose.yaml` `System__Mode: RESPONSE_PUBLISHER` |
| dpdapi | DPD tracking API | external | HTTP | Carrier endpoint, URL comes from `DPD:Xml:EndPoint` or `DPD:Json:EndPoint` | `XML/DPDClient.cs:86`, `JSON/DPDClient.cs:68` (no prod URL in the repo) |
| ccm | carrier-credentials-manager | service | HTTP API | Source of per-contract credentials | `CarrierCredentialsProvider.cs:237`; base URL from `CarrierCredentialsService:Endpoint` (e2e: `/api/carriers/DPD`) |
| mongo | Parcel collection | store | MongoDB | Holds `ParcelNumber`, `LatestTrackingNumber`, `LastRequestedAt` | `DataAccess/Model/Parcel.cs`; database and collection from `ParcelRepositoryOptions` (e2e: `tracking-core` / `connector-dpd-parcels`) |
| etcd | Connector config | store | etcd | Framework batch options and mapper settings, reloaded on change | `Program.cs:97,110-111` |
| kube | Kubernetes probes | external | HTTP | Probable caller of the health endpoints | Not confirmed |

## Relationships

| from | to | label | protocol / topic | confirmed |
| --- | --- | --- | --- | --- |
| worker | bc | GetBatch | gRPC server stream | yes |
| worker | rh | each tracking request | in-process | yes |
| worker | streamer | stream of responses | in-process | yes |
| streamer | rp | SendResponse | gRPC client stream | yes |
| rh | provider | TrackParcel | in-process | yes |
| provider | xml | Track (default) | in-process | yes |
| provider | json | Track (if DPDApiVersion=json) | in-process | yes |
| xml | creds | get credentials by contract | in-process | yes |
| creds | ccm | GET credentials | HTTP | yes (path shape only in e2e config) |
| xml | dpdapi | POST XML request | HTTP `text/xml` | yes |
| json | dpdapi | POST JSON, apikey header | HTTP JSON | no (code exists; prod use unknown) |
| xml | repo | get / upsert latest number | in-process | yes |
| json | repo | get / upsert latest number | in-process | yes |
| xml | xmlmap | map response | in-process | yes |
| json | jsonmap | map response | in-process | yes |
| repo | mongo | find / upsert parcel | MongoDB wire protocol | yes |
| host | etcd | load and watch config | etcd | yes |
| host | repo | --init: create unique index | in-process | yes |
| kube | health | GET /healthz, /readyz | HTTP | no |

## Not confirmed / open questions

- **UNKNOWN** **JSON client use in prod (edge `json` to `dpdapi`).** `Program.cs:171-176` selects the JSON client when `System:DPDApiVersion` is `json`; the default is `xml` (`SystemSettings.cs`). The e2e config never sets it. The repo does not hold the prod value. The Waypoint overview says nothing calls the JSON client; the source contradicts that, because the host registers it.
- **UNKNOWN** **Kubernetes probes (node `kube` and its edge).** The repo has no deployment manifest. The probe endpoints exist in code; the only hint at a caller is the Waypoint `deploy: k8s` field.
- **UNKNOWN** **Framework internals.** Read in tracking-core at c081108, not in the NuGet package the connector builds against. Both are version 0.6.2, so the match is probable but not proven.
- **UNKNOWN** **Credential pause.** Waypoint says this is the only connector that pauses a contract after a credential error. In this repo the connector only returns a `CREDENTIALS_ERROR` response (framework `TrackingRequestHandler.cs:58`). Any pause happens downstream and is not drawn.
- **UNKNOWN** **Prod endpoints and DPD host.** DPD URL, DPD Local URL and collection names are config; only e2e values were visible. The Waypoint claim "geopostuk XML API" does not appear in source.
- **UNKNOWN** **Fuse MCP.** `lookup-service connectors-dpd` returns not found, so no neighbour fact was cross-checked there.
- **UNKNOWN** **Left out on purpose.** Datadog logs and StatsD metrics (`Program.cs:198-223`), and the topics downstream of response-publisher. This keeps the diagram inside the container boundary and the 20-node cap.

## Sources

- connectors-dpd at fad40eb7e7c09a9cbece1e0cdb773c9ff92c8787 (HEAD, clean tree): `src/Gfs.Fenghuang.Connectors.DPD/Program.cs`, `HealthChecks/*.cs`, `appsettings.json`; `src/Gfs.Fenghuang.Connectors.DPD.Core/` (`DPDTrackingProvider.cs`, `IDPDClient.cs`, `XML/*`, `JSON/*`, `Security/*`, `DataAccess/*`, `Settings/*`); `e2e/docker-compose.yaml`; `README.md`.
- tracking-core at c081108 (read-only): `src/Gfs.Fenghuang.Tracking.Core.Frameworks.Connector/` (`Package/ContainerExtensions.cs`, `Package/SimpleInjectorAddOptionsExtensions.cs`, `Tracking/Batch/CarrierConnectorWorker.cs`, `Tracking/Batch/BatchRequestHandler.cs`, `Tracking/TrackingRequestHandler.cs`, `Tracking/TrackingResponseStreamer.cs`).
- Waypoint `Engineering/connectors-dpd/waypoint.yaml` and `overview.md` (verified_sha fad40eb, equal to HEAD, so not stale); context only.
- Fuse MCP `lookup-service`: no entry.
