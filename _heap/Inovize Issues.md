
# Security

## Executive summary

Two integrations leak live, reusable credentials in cleartext inside functional documentation that has been exported to a shared OneDrive location:

| #   | Business                   | System                           | What leaked                                        | Severity        | Customer data at risk                                            |
| --- | -------------------------- | -------------------------------- | -------------------------------------------------- | --------------- | ---------------------------------------------------------------- |
| 1   | **Iconic**                 | Shopify Admin API                | 3 storefronts' access tokens **+ paired API keys** | **HIGH**        | Yes - direct read access to orders/customers (PII)               |
| 2   | **Charlotte Tilbury (UK)** | eShopWorld carrier/logistics API | OAuth2 `client_id` + `client_secret` (full-scope)  | **MEDIUM–HIGH** | Yes - carrier shipment/consignee data (validity to be confirmed) |

**7 distinct secret values** were found, across 2 systems / 2 of 10 businesses, forming 4 usable credential sets:

* 3x Shopify access tokens (`shppa_` prefix)
* 3x Shopify API keys (Basic auth)
* eShopWorld `client_secret`

This is important: a credential in a document is exploitable by anyone who can read the document. An attacker can use the credential directly against Shopify or eShopWorld. Both credential sets are long-lived and reusable, and the affected storefront URLs are disclosed alongside the tokens, so no discovery step is required. 

Due to how these have been shared, we are unsure if the best practice in encryption at rest and in transit have been followed.

There is also immediate action required. The three Shopify tokens/keys need rotating now (they front live customer PII), then validate and rotate the eShopWorld secret. Purge the values from every copy - including OneDrive version history - and gate future exports through a secret scan.

---

# Consistency

Issues lie within functional documentation:

- Consistent structural template with variable, fluent prose inside it 
	- The documents make use of an identical section skeleton across clients:
		- Purpose & Audience
		- Integration Estate
		- Interface Inventory
		- per-domain breakdowns 
	- However, the sentences aren't fill-in-the-blank. They vary in length, clause structure, and connective phrasing between documents.
- Synthesizing language a template wouldn't produce the following: 
	- "the named queue is the single literal that links an interface's legs," 
	- "the second seam...is REST, not a queue"
	- These are explanatory framings that require understanding the system to phrase, not just fields dropped into a slot.
- Editorial asides / judgment calls: 
	- things like flagging a hard-coded fallback as "worth reviewing at cut-over,",
	- or calling a leftover label "vestigial.".
	- A deterministic extractor doesn't have opinions about what's worth flagging.
- Audience-aware framing repeated near-identically in wording but reworded per client: 
	- every doc opens by explaining it's "written for the migration and onboarding engineers who will move these flows onto a new platform" - same intent, differently phrased each time, which is what an LLM does when re-running the same prompt template against different input data rather than a hand-written boilerplate.
- The "Generated from the deterministic technical pack" banner itself is a tell in what it doesn't say: 
	- it's careful to describe the input as deterministic (structured facts pulled from the Jitterbit projects), 
	- this is consistent with the following flow: deterministic extraction, followed by a LLM writing the narrative from that structured data. 
	- If a human had written these, you wouldn't see a machine-stamped ISO timestamp banner identical to the second, across 11 unrelated clients.