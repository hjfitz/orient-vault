---
tags: [handover, diagram-twin]
page: Carrier Proxies and Labelling (MPK 353697822), section "What a proxy does"
level: C4 component
status: draft for Harry's review, not yet drawn
---
# Component diagram: a carrier proxy

This diagram shows the parts of one generic carrier proxy and the systems it talks to when Selector asks for a label. It does not show any single carrier's quirks, the other operations (cancel, manifest, status), tracking, or the Selector internals.

## Groups

| Name | Boundary type | Contents |
| --- | --- | --- |
| Carrier proxy | Container: one Node.js and Express service. GKE workload in `prod-uk1-primary-cluster` for most proxies, Cloud Run for FedEx and InPost | E3, E4, E5, E6, E7, E8 |

Everything else sits outside the group. The credential stores (E9, E10) are drawn outside because the pages do not say where they run.

## Elements

| ID | Name | C4 type | Technology or GCP product | Description | Group | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | Selector site (CSS or Client4) | system | | Legacy Selector at a customer site. Calls the proxy URL held in the site's CUST_SITES row. Stores the shipment and prints the label from the response. | none | Page 353697822, "What a proxy does", Caller row | Verified in page |
| E2 | ApiKy | system | | GFS service that checks an API key and returns the customer's profile. | none | Page 353697822, Auth row | Verified in page |
| E3 | Request handler and key check | component | Node.js, Express | Receives the POST, reads x-api-key (the ApiKy key on the customer's contract) and asks ApiKy who the customer is. | Carrier proxy | Page 353697822, "What a proxy does" step 1 | Verified in page |
| E4 | Credentials lookup | component | Node.js | Turns the customer profile into the customer's carrier account, or GFS's shared account. | Carrier proxy | Page 353697822, step 2 and Credentials row | Verified in page |
| E5 | Carrier token handler | component | OAuth | Gets an OAuth token from the carrier and caches it. Only carriers that use OAuth need it. | Carrier proxy | Page 353697822, step 3. `Engineering/ups-proxy/overview.md` (cached for its lifetime minus 60 seconds) | Verified in page |
| E6 | Request mapper | component | Node.js | Maps Selector's request into the carrier's API format. UPS forwards Selector's old XML unchanged. | Carrier proxy | Page 353697822, step 4 and "Why they exist" (UPS) | Verified in page |
| E7 | Carrier client | component | HTTPS, REST or XML | Calls the carrier API with the mapped request and the credentials or token. | Carrier proxy | Page 353697822, step 5 | Verified in page |
| E8 | Response mapper | component | Node.js | Turns the carrier's reply into a label, tracking numbers and errors in Selector's shape. | Carrier proxy | Page 353697822, step 6 | Verified in page |
| E9 | Customer credentials in MongoDB | datastore | MongoDB | Per-customer carrier credentials, found through an ID in the ApiKy profile. | none | Page 353697822, Credentials row. `Systems/carrier-integrations/architecture.md` (keyed by an ID in the ApiKy profile) | Verified in page |
| E10 | Shared GFS carrier account | datastore | | One GFS carrier account used for every customer. Where it is stored is not stated. | none | Page 353697822, Credentials row | Not confirmed |
| E11 | Carrier API | system | | The carrier's own REST API, plus its OAuth token endpoint. UPS also takes legacy XML. | none | Page 353697822, steps 3 and 5 | Verified in page |

Counts: 11 elements, made up of 3 systems (E1, E2, E11), 6 components (E3 to E8) and 2 datastores (E9, E10).

## Relationships

| From ID | To ID | Label | Technology or message | Status |
| --- | --- | --- | --- | --- |
| E1 | E3 | Post a label request with the customer's key | HTTPS POST to the proxy URL, header x-api-key | Verified in page |
| E3 | E2 | Check the key and fetch the customer profile | HTTPS GET /api/profile | Verified in page |
| E3 | E4 | Pass the customer profile on | In-process call | Verified in page |
| E4 | E9 | Look up this customer's carrier credentials | MongoDB query | Verified in page |
| E4 | E10 | Use the shared GFS account when the proxy has no per-customer one | Not stated | Not confirmed |
| E4 | E5 | Hand over credentials so a carrier token can be fetched | In-process call | Verified in page |
| E5 | E11 | Request an OAuth token and cache it | OAuth token request | Verified in page |
| E5 | E6 | Pass credentials and token to the mapping step | In-process call | Verified in page |
| E6 | E7 | Send the request in the carrier's format | In-process call | Verified in page |
| E7 | E11 | Call the carrier to create the label | HTTPS, REST (UPS: legacy XML) | Verified in page |
| E7 | E8 | Pass the carrier's reply on | In-process call | Verified in page |
| E8 | E1 | Return the label, tracking numbers and errors | HTTPS response: base64 PDF, PNG or ZPL | Verified in page |

Counts: 12 relationships. The carrier's reply to E7 and ApiKy's reply to E3 travel back on the same arrow, so they are not drawn separately.

## Layout hint

Put Selector (E1) at far left and the proxy group in the middle, with the six steps running left to right in page order. Put ApiKy (E2) above the group and the two credential stores (E9, E10) below it. Put the carrier API (E11) at far right and draw the label return (E8 to E1) as the one long arrow back along the bottom.

## Key needed

- Dashed box or arrow with the label `Not confirmed`: the item is not proved by any source I read (E10 and its arrow).
- Cylinder: a datastore. Plain rectangle: a component or an external system.
- Arrows run in the direction of the request. A reply that comes back on the same call is not drawn.
- No GCP icon on the boxes. The group carries the GKE icon, with a note "Cloud Run for FedEx and InPost". No Pub/Sub, Memorystore or other product appears here.
- Credential patterns by proxy (text only, not boxes):
  - MongoDB, per customer: Royal Mail, FedEx, InPost, Exelot, DPD Europe (KMS-encrypted).
  - ApiKy profile: BJS (the carrier secret sits in the profile, so E4 reads it from the profile E3 already holds).
  - One GFS account: UPS (one OAuth client), OCS, Coll8.
  - Not checked: Amazon.

## Gaps

- **E10 storage is unknown.** The pages say "one GFS account for everyone". They do not say if it sits in an environment variable, a secret or a config file. I drew it dashed.
- **The ApiKy profile feeds E4 in every case, not only for BJS.** `Engineering/royal-mail-proxy/overview.md` says the profile's `royalmailCustomerId` selects the Sapient account. `Engineering/coll8-proxy/overview.md` says Coll8 still reads `accountCode` from the profile. So "one shared GFS account" for Coll8 is not the whole story. Source: vault notes from code at `361de96` and `44a05c3`.
- **ApiKy's role differs for UPS.** `Engineering/ups-proxy/overview.md` says ApiKy "validates the key only" for UPS. The page says ApiKy returns the profile. Both are true for the generic case, but UPS ignores the profile.
- **The token cache location is not stated.** The page says "cached". The UPS note gives the lifetime (token life minus 60 seconds). Whether the cache is in memory or Redis is Not confirmed, so E5 has no datastore.
- **E5 does not apply to every proxy.** Only UPS and Royal Mail are known to use OAuth. Which of the others fetch a token is Not confirmed.
- **Hosting conflict on Amazon.** The page table puts the Amazon proxy on Azure DevOps and GKE, but its Sources list the code under GitHub `amazon-proxy`. `Systems/carrier-integrations/architecture.md` says "source not located". It does not change this diagram, which keeps to one generic proxy.
- **The dev rewrite is not what this shows.** `Engineering/carrier-proxies/overview.md` describes a GitHub monorepo rewrite of UPS, OCS, Coll8 and Exelot on `api-host-framework`. It runs in dev only. This diagram describes the production originals. In the rewrite, Exelot keys each need an ApiKy profile with `exelotPartnerId`, which sits oddly beside the page's "MongoDB, per customer" for Exelot. Not confirmed which is true in prod.
- **"Every proxy checks the key with ApiKy" is not proved.** `Systems/carrier-integrations/known-context.md` notes two proxies that ignore their configured ApiKy URL through a typo. It does not name them.
- **Operations beyond create label are not drawn** (cancel, manifest, status, service codes, customs documents, access points). The page says some proxies do these. One box per step would be needed to show them.
- **No numbers were re-checked against Datadog.** Traffic figures are not on the diagram, so this does not affect it.
