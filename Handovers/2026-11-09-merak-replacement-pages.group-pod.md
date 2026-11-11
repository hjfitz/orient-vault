This group answers how GFS gets a proof of delivery (POD): the signatory, delivery time and signature or safe-place photo. The most useful fact is that a POD is not a tracking event. It never reaches `raw_tracking.v1`. `gfs-pod-service` calls the carrier's own API live when someone asks, and returns one normalised POD. It handled about 21k requests in the 15 days to 6 Nov 2026, and DHL Parcel UK made up about 84% of them. That window is the one the page used, and the figures were not re-run on 23 Oct to 7 Nov.

Tags appear where the source research gives one.

## What is in this group

| Page | The question it answers | State |
| --- | --- | --- |
| [Proof of Delivery Service](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/353861642) | What does the POD service do, who calls it, and how much traffic does it carry? | Live |
| [How Each Carrier's POD Is Retrieved](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/354877489) | For each carrier, which calls fetch the POD, where does the image come from, and what can go wrong? | Published draft, unverified (code read at `d1f0ada`) |

## What we know

- The service calls each carrier's POD or tracking API on request. It owns the per-carrier calls and the image handling, such as base64 decoding and cropping PDFs and TIFFs.
- In the 15 days to 6 Nov 2026 it received 20,978 requests and served 19,194 PODs and 5,545 images. It sent 203 POD emails. About 17.6k requests were for DHL Parcel UK.
- Callers use the in-cluster v2 API, keyed on the GFS shipment ID. They are the customer portal, the Connect API and the Nexus staff app. A public v1 API exists, and no caller of it was found.
- Eleven carriers are wired in, plus a test carrier. Four got no requests: Yodel, Panther, Tuffnells and FedEx. Royal Mail, the busiest proxied carrier, has no POD support.
- There are three ways to get an image. UPS returns it inline. BJS has no API, so the module scrapes a web page. Every other carrier needs a second call.
- **CONFIRMED** `dhl-pod-images` exists. Only the UK Mail SOAP module calls it. Prod sets the flag that moves DHL Parcel UK to the eCommerce REST module, which takes images from DHL's own URLs.
- **CONFIRMED** DPD Local posts the parcel number it is given. It is not on the consignment POD list, so a caller must name the parcel.
- The v2 API returns GFS's own geocoded shipment address. The v1 API keeps the carrier's address. The two share a cache key. Five modules treat the carrier's local time as UTC or as the server's time zone: UK Mail, Evri, UPS, Panther and Tuffnells.

## Where to start

1. Proof of Delivery Service, for the service, its callers and its traffic.
2. How Each Carrier's POD Is Retrieved, for the per-carrier detail.

## Not confirmed yet

- **Which parcel callers ask for on the v2 route.** The service does not pick the delivered parcel for DPD Local. Who does is open.
- **Request errors against requests.** About 25.9k errors exceed about 21k requests. Not-found PODs counted per call are a likely part.
- **The public v1 API.** Whether anything still calls it is open.
- **The DHL Express module.** The page says it is not loaded and does not work. The cleanup pass did not re-check it.
- **Per-carrier POD traffic.** The figures were not re-run on the canonical window.
- **POD details in tracking events.** Whether carriers with no POD module send them, such as a signatory in the Royal Mail webhook, is open.
- **Credentials service.** When `gfs-carrier-credentials` is replaced by `carrier-credentials-manager` is open.

## Related groups

- [Tracking: How GFS Follows a Parcel](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357597186) covers the tracking events that sit beside the POD route.
- [Carriers and How We Integrate With Them](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357629953) covers which carriers GFS uses and how data moves to and from them.
- [ECM Platform: How a Shipment Moves Through It](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/357662721) shows where the POD sits in a shipment's whole path.
- [1. Research into Existing Services](https://globalfreight.atlassian.net/wiki/spaces/MPK/pages/351502339) is the research root.
