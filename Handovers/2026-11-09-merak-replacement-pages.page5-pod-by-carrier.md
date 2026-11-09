`gfs-pod-service` has one module per carrier, and each fetches a proof of delivery (POD) in its own way. This page lists, carrier by carrier, the calls each module makes, how it authenticates, what it reads from the response, where the image comes from and what can go wrong. It was written from the code on 9 Nov 2026. Nothing was run and no carrier was called.

It extends [Proof of Delivery Service](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353861642/Proof+of+Delivery+Service), which covers the service, its APIs, its callers and its traffic. The code is `origin/master` at `d1f0ada`, two pull requests (14257 and 14259) after the `811007e` that page cites. They moved FedEx from the parcel list to the consignment list and fixed the key FedEx documents arrive under.

## In short

- **Eleven carriers are in service, plus a test carrier.** DHL Parcel UK uses one of two modules, chosen by a flag the repo does not set. A DHL Express module exists, but it is not loaded and does not work.
- **There are three ways to get an image.** UPS returns it inline in the tracking response. BJS has no API, so the module scrapes a web page. Every other carrier needs a second call.
- **UPS and FedEx call their APIs with one GFS account for every customer.** FedEx has a per-customer path in the code, and it is commented out.
- **Five modules treat the carrier's local time as UTC or as the server's time zone.** These are UK Mail, Evri, UPS, Panther and Tuffnells.
- **No module sets a timeout.** Only FedEx and DHL eCommerce retry, and only once, after a 401.

## The carriers at a glance

| Carrier | ID | Looks up by | POD per | Credentials | Image comes from |
| --- | --- | --- | --- | --- | --- |
| DHL Parcel UK, eCommerce module | 31 | Consignment number | Consignment | A GFS client ID and secret from the environment | A second call to DHL |
| DHL Parcel UK, UK Mail module | 31 | Consignment number | Consignment | One carrier-wide login from the credentials service | A URL in the SOAP response |
| DPD | 10 | Tracking number | Parcel or consignment | An API key from the credentials service, fetched on every call | A second call, base64 in JSON |
| DPD Local | 19 | Parcel number | Parcel | The same as DPD, with its own key | The same as DPD |
| Evri | 16 | Barcode | Parcel or consignment | A token from `evri-auth-facade`, plus an API key from the credentials service | A second call to a link in the event, base64 in JSON |
| UPS | 32 | Tracking number | Parcel or consignment | One GFS OAuth client from the environment | Inline in the tracking response, base64 |
| FedEx | 11 | Tracking number | Consignment | One GFS OAuth client from the environment | A second call to the documents API, base64 PNG |
| Yodel | 34 | Consignment number, used as the Yodel parcel ID | Consignment | One carrier-wide client from the credentials service | A second call, raw bytes |
| Panther | 24 | Consignment number and contract | Consignment | An API key per contract from the credentials service | A second call. A PDF is converted and cropped |
| Tuffnells | 30 | Consignment number, contract and postcode | Consignment | The contract as the account code. No token | A second call. A TIFF is converted and cropped |
| BJS | 41 | The GFS shipment record | Consignment | None | A scrape of a BJS web page, then a second call |
| Amazon Logistics UK | 1 | Tracking ID, plus customer and service code from the shipment | Consignment | One API key from the environment, sent to the Amazon proxy | A second call to a pre-signed URL |
| Test carrier | 35 | Consignment number | Consignment | Environment settings | None. It returns the stored image reference as bytes |
| DHL Express | Not loaded | Consignment number | Consignment | Not usable | Not usable |

Which carrier IDs the v2 API accepts comes from two lists in `src/config.js`. Parcel POD: 10, 16, 19 and 32. Consignment POD: 1, 10, 11, 16, 24, 30, 31, 32, 34, 35 and 41.

## Delivery time, by carrier

| Carrier | What the module does with the carrier's time |
| --- | --- |
| UK Mail | Formats local wall-clock time and labels it UTC with a `Z` |
| Evri | Converts to London time and labels it UTC with a `Z`, so the value is an hour out in summer |
| UPS | Builds a date from the event's date and time strings in the server's time zone. It is correct only if the process runs in UTC |
| Panther | Builds a UK date as if it were UTC, with no summer-time handling |
| Tuffnells | Builds the date from the wall-clock time as if it were UTC |
| DPD | Reads a UTC value ending in `Z` |
| DHL eCommerce | Expects an ISO value ending in `Z` and does no conversion |
| FedEx | Parses a value that carries an offset |
| Yodel, Amazon, BJS | Pass the carrier's value through unchanged |

## DHL Parcel UK

The carrier is ID 31, called UK Mail in the code. One flag chooses the module: `DHLECOMMERCEUK_USEINSTEADOFUKMAIL`. If it is `true`, the service uses the DHL eCommerce module. Otherwise it uses the UK Mail module. The parent page records the production setting as on. The repo's deployment file does not set it.

### DHL eCommerce UK (REST)

- **Calls.** `POST /auth/v1/accesstoken` with a form body. `GET /tracking/v1/shipments?trackingNumber=` with the consignment number. `GET /tracking/v1/images/{imageRef}` for each image. The base URL is `https://api.dhl.com/parceluk`.
- **Auth.** A client ID and secret from the environment. The token is cached with no expiry. After a 401 the module authenticates again and retries once.
- **Delivered means** the shipment's status code is `delivered`. The module reads the first shipment only.
- **Reads.** The signee, the delivery time, the remarks on the delivered events (joined into the driver comments), the receiver's address and the piece count. It sets no special instructions.
- **Image.** The POD document URL and the signature URL from the response. Multi-parcel shipments are not supported.
- **Watch for.** An empty `shipments` array or a missing `events` list throws a type error instead of a not-found error. The code carries a note that no sample data existed to test the remarks.

### UK Mail (SOAP)

- **Calls.** A SOAP `Login`, then `ConsignmentTrackingGetFullDetailsV3` with the consignment number. A later fetch of each image URL.
- **Auth.** One carrier-wide login from the credentials service, fetched on every call. The module sends the token, and also the user name and password in each request. The cached token is set to expire in 2099, so it never refreshes.
- **Delivered means** a status event whose description is `delivered`. The module uses the last one.
- **Reads.** The signee and comments from the first POD entry with a quantity above 0, the address, the special instructions and the declared quantity.
- **Image.** The signature image URL from the first POD entry. Other images are keyed by the delivery type code. If `DHL_POD_IMAGES_ENABLE` is `true`, a lookup at `imageHrefResolver` replaces the image URLs. Its default is `http://localhost:8765`.
- **Watch for.** If that lookup fails, it returns nothing and wipes the signature image. There is no timeout and no check that an image fetch succeeded.

## DPD and DPD Local

DPD is ID 10, and DPD Local is ID 19. DPD Local reuses the DPD module with its own name and its own credentials key.

- **Calls.** `POST https://api.customers.dpd.co.uk/tracking/v1/customer/parcel/tracking` with the tracking number. For an image, `GET` the parcel or consignment image path with the image key.
- **Auth.** An `apikey` header. The key comes from the credentials service on every call, with no caching.
- **Delivered means** the first event with code `001`, or with `delivered` anywhere in its type or description.
- **Reads.** The signee and the parcel code (as the shipment reference) only. It does not read comments, a location, an address or an item count.
- **Image.** A second call returns JSON with a base64 image. A key starting `S5^`, or a lone key, becomes the POD image. Any other key becomes the signature.
- **Watch for.**
    - The match on `delivered` would also match "not delivered".
    - The two 404 checks read `statusCode`, which a node-fetch response does not have, so they never match.
    - The image path for consignment lookups references variables that are not in scope.
    - DPD Local has no consignment route in v2.

## Evri

Evri is ID 16, called Hermes in the code.

- **Calls.** `GET https://api.hermesworld.co.uk/client-tracking-api/v1/events?barcode=…&descriptionType=CLIENT`. For an image, `GET` the link the event carries.
- **Auth.** A bearer token from `http://evri-auth-facade:3000/token`, plus an `apikey` header from the credentials service. The module caches the token without a safety margin and does not retry after a 401.
- **Delivered means** any event with a `signatures` or `safe-place-photos` link.
- **Reads.** The delivery time, converted to London time. GPS from the event's location, skipped when both values are 0. The address is looked up from the GPS point. The signee, comments and item count are always empty.
- **Image.** The first link becomes the POD image, and the other links are added under their link names. A second call returns a JSON array, and the module decodes the first entry's base64 field.
- **Watch for.**
    - A 401 or 403 becomes an unauthorised error, a 500 becomes a generic error, and any other failure, including 429 and 502, becomes a not-found error.
    - An error event prints as `[object Object]`.
    - The image link is fetched with the token and API key and is not checked against Evri's host.

## UPS

UPS is ID 32, and it is the only carrier that returns its images inline.

- **Calls.** `POST https://onlinetools.ups.com/security/v1/oauth/token` with basic auth. `GET https://onlinetools.ups.com/api/track/v1/details/{trackingNumber}?locale=en_GB&returnSignature=true&returnPOD=true`.
- **Auth.** One GFS OAuth client from the environment, for every customer. The credentials service is assigned in the code but never called. The token is cached and refreshed on expiry, with no retry after a 401.
- **Delivered means** an activity with status code `D`, or `011`, or a description containing `delivered`.
- **Reads.** The signee from `receivedBy`, the delivery location as the driver comment, the package count, the reference numbers and the address. The module reads the first package only.
- **Image.** The signature is base64 in the response. The photo is included only when the photo indicator is `Y` and the disposition code is `V`. The whole base64 image sits in the cached POD. The configured type is `image/jpeg`, and the actual format is not stated in the code.
- **Watch for.** A response with an error but no `errors` list throws a type error. The token request sends a literal `string` as the merchant ID.

## FedEx

FedEx is ID 11. It uses consignment lookups only since 6 Nov, when PR 14257 moved it off the parcel list.

- **Calls.** `POST /oauth/token`. `POST /track/v1/trackingnumbers` with the tracking number. `POST /track/v1/trackingdocuments` for the image, asking for `SIGNATURE_PROOF_OF_DELIVERY` as a PNG. The host is `apis.fedex.com`.
- **Auth.** One GFS client from the environment. The per-customer route is commented out in the code: it fetched a child key per contract and used the `csp_credentials` grant. The cached token expires 60 seconds early, and a 401 triggers one retry.
- **Delivered means** the shipment has an `ACTUAL_DELIVERY` date.
- **Reads.** The signee from `receivedByName`, the location description as the driver comment, the delivery address, the item count and the shipper reference. The module reads the first track result only.
- **Image.** The image is offered only if the available images include the signature type. A second call returns a base64 PNG, which the module reads from `output.documents[0]`. PR 14259 changed that key from `document`. The call needs the contract.
- **Watch for.** If an image call fails, the error handler refers to a variable that is out of scope, so the caller sees a reference error instead of an image-not-found error.

## Yodel

Yodel is ID 34.

- **Calls.** `POST` to the token URL with a form body and the `tracking` scope. `GET {apiBaseUrl}/parcel-tracking/{consNo}` with a bearer token and an `x-ibm-client-id` header. For an image, `GET {apiBaseUrl}{imageRef}`.
- **Auth.** One carrier-wide client from the credentials service. The credentials are fetched on every call, and the token is cached.
- **Delivered means** the first event whose description starts with `Delivered`, or whose status group is `DELV`.
- **Reads.** The signee, the comments and the GPS point. If there is no GPS point, it uses the delivery location. The address is looked up from the GPS point.
- **Image.** The delivery event's POD image URI becomes the POD image. Other events with a URI are added under their descriptions. The module returns raw bytes.
- **Watch for.** An event with no description throws a type error. The key for extra images replaces only the first space. The reverse lookup is not guarded if the lookup service is missing.

## Panther

Panther is ID 24.

- **Calls.** `GET {apiBaseUrl}/apiv2/public/get_order?key=…&order={consNo}&json=1`. The API key is in the query string. For an image, `GET` the PDF or photo, using the portal host for a `.pdf`.
- **Auth.** An API key per contract from the credentials service, with no caching. The image fetch sends no authentication.
- **Delivered means** the status is `delivered`.
- **Reads.** The delivery time from the last signed POD entry, as a UK date. The address, the item count (summed from the lines) and GPS from the photos. It does not read a signee or comments. The shipment reference is the consignment number.
- **Image.** The POD image is the PDF, or the first photo if there is no PDF. The module writes the PDF to a temporary file, converts it with the external `mutool` program and crops a fixed region of page 1 into a 200 by 200 PNG. It returns photos as raw bytes.
- **Watch for.** Temporary files are never deleted. A response whose consignment number does not match throws an error that prints `[object Object]`. There is no check on the HTTP status.

## Tuffnells

Tuffnells is ID 30.

- **Calls.** A SOAP call, `GetTrackingRecordPostcodeAsync`, with the contract as `AccountCode`, the consignment number as `Reference` and the postcode. For an image, `GET` the TIFF URL from the response.
- **Auth.** None in the code beyond the account code. If the response's `Authorised` field does not start with `Authorised`, the module throws an unauthorised error. A missing contract or postcode throws a missing-parameters error.
- **Delivered means** the first movement with delivered packages and a movement date.
- **Reads.** The signee, the item count, the shipment reference, the special instructions and the address. It does not read comments.
- **Image.** The module converts the TIFF to a PNG with `sharp` and crops a 233 by 78 region.
- **Watch for.** The image URL is `http`, with no host check. A response with no POD image list throws a type error.

## BJS

BJS is ID 41. It has no POD API, so the module works from GFS's own copy of the shipment and a BJS web page.

- **Source of the link.** When a BJS tracking event arrives with status `BEP1910` or `BEP1935`, the tracking subscriber takes a `{"url": …}` fragment from the status description and stores it on the shipment record.
- **Calls.** The module reads the shipment from Mongo, which needs the shipment ID. It then `GET`s the stored page URL and finds the first signature image under `https://epod.bjshomedelivery.com`. For the image, it makes a second `GET`.
- **Auth.** None.
- **Reads.** Only the reported date, unchanged, and the image. It sets no delivered flag, signee or GPS.
- **Watch for.** The v1 API passes no shipment, so BJS fails there. The module rejects without returning in several places, so the code after the rejection still runs. A shipment with no stored link gives a not-found error.

## Amazon Logistics UK

Amazon Logistics is ID 1. The module calls the internal Amazon proxy, not Amazon.

- **Calls.** `GET {AMAZON_PROXY_API_BASE_URL}/shipping/tracking/{channelType}/{customer}/{trackingId}`. The channel type comes from the service code: `SFPA` gives `sfp-amazon`, `SFPE` and `SFPS` give `sfp-evri`, and anything else gives `external`.
- **Auth.** An `X-API-Key` header from the environment. The module throws if the base URL or key is missing. The image fetch sends no authentication.
- **Needs.** The customer and service code from the GFS shipment, so only v2 works.
- **Delivered means** the newest event has the code `delivered`, or the tracking summary is `delivered`.
- **Reads.** The signee from `receivedBy`, GPS from the proof of delivery, and the address from the event's location. If GPS is missing, the module looks one up from the address.
- **Image.** The signature and delivery image URLs. They are pre-signed and expire after days, which is longer than the one-hour cache.
- **Watch for.** A 404 gives a not-found error, and any other failure gives a generic error.

## Test carrier and DHL Express

- **The test carrier (ID 35)** is loaded in production. It fetches a token on every call, always reports `delivered`, and returns the stored image reference as bytes without fetching anything.
- **DHL Express** is not in the loaded list. Its production URL is `???`. In the module, the image call refers to a variable that does not exist, and the response is read as if it came from another carrier. Treat it as unfinished.

## Behaviour all the modules share

- **Cache.** A POD is cached under `carrierId:consNo`, or `carrierId:consNo:parcelNo` for a parcel, for 3,600 seconds. An image is cached under `carrierId:consNo:imageName`, with no parcel number. Images from different parcels of one consignment can collide, which matters for DPD, DPD Local, Evri and UPS.
- **Address.** When the caller supplies a GFS shipment, the service replaces the carrier's address with the shipment's own and geocodes it. This happens for every carrier.
- **Image type.** The v2 image route sets `Content-Type` from the carrier's configured type, not from the bytes.
- **Credentials.** The credentials service is called as `GET /ccs/{carrier}/{contract}` with a bearer token. A result with a contract number is stored per contract.
- **Config files.** Nothing in the repo loads `carrier-config.prod.yml`, and parts of it disagree with `config.js`. Treat it as unused.

## Not confirmed yet

- **The production environment values.** The repo does not show `SUPPORTER_PARCEL_POD_CARRIERS`, `SUPPORTER_CONS_POD_CARRIERS`, `DHLECOMMERCEUK_USEINSTEADOFUKMAIL`, `DHL_POD_IMAGES_ENABLE`, `DHL_IMAGES_URL` or `AMAZON_PROXY_API_BASE_URL`.
- **The name `dhl-pod-images`.** The parent page says DHL images come through an internal service of that name. The repo has no such name, only the `imageHrefResolver` setting.
- **How DPD Local picks a parcel.** The parent page says it picks the delivered parcel. The module only uses the parcel number the caller sends. The v2 route was not checked.
- **Whether the v2 route passes the contract and postcode** that Tuffnells, FedEx and Panther need.
- **The real image format from UPS.** Only the configured type is in the code.
- **Behaviour against live carriers.** This is a code read. No carrier API was called.

## Sources

- **Code:** Azure DevOps `GFS POD/GFS POD` at `origin/master` `d1f0ada`: `src/pod-service/*-service.js`, `load-services.js`, `pod-cache.js`, `credentials-service.js`, `token-service.js`, `src/config.js`, `src/subscriber/handlers/tracking.js`, `src/api-v2/routes/get-parcel-pod-image.js` and `carrier-config.prod.yml`.
- **Parent page:** [Proof of Delivery Service](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353861642/Proof+of+Delivery+Service), written from `811007e`.
