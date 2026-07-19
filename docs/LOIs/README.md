# Letters of Intent (LOIs) — Mantle Protocol Partnerships

This directory contains Letter of Intent templates for Mantle ecosystem protocols.
LOIs strengthen grant applications by demonstrating real demand for the product.

---

## What is an LOI?

A Letter of Intent is an informal, non-binding statement from a protocol team expressing interest in using Mantle Intel Agent's on-chain intelligence services. It is **not a contract** — it signals intent and validates product-market fit.

## Why LOIs Matter for Grants

Grant reviewers (Mirana Ventures, Mantle Foundation) want to see:
1. **Real demand** — Protocols that would actually use the product
2. **Market validation** — Not just the founder's opinion that the product is needed
3. **Partnership potential** — Evidence of ecosystem integration

Even **1 signed LOI** materially strengthens an application. 3+ is exceptional.

---

## Current LOI Status

| Protocol | Status | Value Proposition | Contact |
|----------|--------|-------------------|---------|
| Lendle | 📋 Template ready | Real-time depeg + liquidation cascade monitoring | [Discord](https://discord.gg/lendle) |
| Merchant Moe | 📋 Template ready | Liquidity imbalance alerts, impermanent loss protection | [Discord](https://discord.gg/merchantmoe) |
| Agni Finance | 📋 Template ready | Whale movement alerts, concentrated liquidity monitoring | [Discord](https://discord.gg/agnifinance) |

---

## How to Get LOIs Signed

### Step 1: Identify the Right Person
- Look for: Head of Product, Head of Risk, or DevRel at each protocol
- Best channels: Mantle Discord (protocol channels), Twitter DMs

### Step 2: Send a Personalized Message
Use the protocol-specific talking points below. Be concise — protocol teams are busy.

**Message template:**
> Hi [Name], I'm building Mantle Intel Agent — a real-time on-chain anomaly detection pipeline for Mantle Network. It currently monitors [protocol-specific data] and I'd love to get your feedback.
>
> Would you be open to signing a brief Letter of Intent confirming that Lendle/Merchant Moe/Agni would find value in real-time [specific feature]? It's non-binding and takes 2 minutes.

### Step 3: Send the LOI
- Share the relevant LOI template below
- Ask them to sign digitally (DocuSign, Google Docs comment, or even a Twitter DM confirmation counts)
- Any form of written confirmation works for grant purposes

### Step 4: Save the Signed LOI
- Save the signed document in this directory as `LOI-[Protocol]-signed.pdf` or similar
- Reference it in your grant application

---

## Protocol-Specific Talking Points

### Lendle
- **Pain point:** Lendle has $XXM TVL in lending pools but no real-time monitoring for depeg events or liquidation cascades
- **Our solution:** mETH depeg detection (fires at ≥50bps deviation), liquidation cascade prediction (2-4hr lead time), health factor monitoring
- **Impact:** "One avoided cascade on Lendle could save $50K+ in bad debt"
- **Integration:** Alerts via Discord webhook to Lendle risk team, custom `lendle_only` subscription filter

### Merchant Moe
- **Pain point:** LPs in Merchant Moe pools have no visibility into reserve imbalances until it's too late
- **Our solution:** Real-time reserve ratio monitoring, imbalance detection at ≥15% shift, whale accumulation alerts near LP positions
- **Impact:** "One LP imbalance alert could save a yield farmer $5K+ in impermanent loss"
- **Integration:** Custom `whale_only` subscription for Merchant Moe LP positions, Telegram alerts for reserve shifts

### Agni Finance
- **Pain point:** Concentrated liquidity positions are especially vulnerable to whale movements and range-bound price action
- **Our solution:** Smart money inflow tracking, cross-protocol correlation detection, whale movement alerts near Agni pools
- **Impact:** "Real-time whale tracking gives Agni users an edge in position management"
- **Integration:** Custom `high_confidence` subscription for Agni-specific pools, API endpoint for Agni UI integration
