---
title: "Automated Firewall Hygiene System"
category: "Security Engineering"
tags: "Palo Alto, Panorama, Python, ServiceNow, Automation, CyberSecurity"
cover: "./assets/firewall_hygiene.png"
read_time: "10 min read"
description: "A 5-stage firewall hygiene workflow that helps identify stale rules, resolve ownership through ServiceNow data, support review decisions, and prepare controlled policy cleanup using Palo Alto Panorama APIs."
---

# Automated Firewall Hygiene System: A Grounded Approach to Stale Policy Cleanups

Managing firewall policies across an enterprise network requires balancing operational uptime with a strong security posture. Over years of operations, security rules inevitably accumulate. Rules created for temporary access, vendor testing, or legacy applications are often abandoned once they are no longer needed. 

This post details the architecture and implementation of an **Automated Firewall Hygiene System**—a closed-loop, 5-stage workflow that coordinates between **Palo Alto Panorama**, **ServiceNow**, and a custom review portal to safely audit, verify, and clean up stale security rules with zero operational downtime.

---

## 1. The Problem: The Accumulation of Stale Security Rules

As enterprise networks grow, firewall rule bloat becomes an inevitability. Obsolete rules present several key challenges:
* **Expanded Attack Surface:** Every active rule that is no longer required is a potential vector for unauthorized access.
* **Compliance & Audit Debt:** Bloated security policies complicate cybersecurity compliance audits, making it difficult to justify active rules.
* **Performance Degradation:** Extremely large, unoptimized policy tables increase the memory overhead and processing time of physical and virtual firewall appliances.

---

## 2. Why Manual Cleanup is Risky and Inefficient

Manually identifying and cleaning up stale rules is highly inefficient and introduces significant operational risks:
* **Lack of Context:** A rule name like `RITM1029384-App-Access` does not tell a security administrator who owns the application today, or if the underlying servers have been decommissioned.
* **Fear of Breaking the Network:** Without verified ownership and usage data, security teams are hesitant to delete policies, fearing they might disrupt a critical business service.
* **Spreadsheet Fragmentation:** Exporting rule tables to spreadsheets and emailing them to application owners leads to ignored threads, outdated tracking, and lost decisions.

To solve this, we replaced manual spreadsheets with a programmatic, human-in-the-loop orchestration pipeline.

---

## 3. System Architecture

The system consists of two primary components designed to operate with minimal external dependencies:
1. **Automation Orchestrator (`overall-FW-Hygeine.py`):** A Python engine that queries APIs, parses rule metadata, maps ticket owners, and automates firewall policy enforcements.
2. **Web Dashboard Server (`dashboard_server.py`):** A lightweight web portal built using Python's standard libraries and backed by an **SQLite database** (`dashboard_runs.sqlite3`). It manages reviewer sessions, Entra ID SSO logins, and stages administrative actions.

---

## 4. The 5-Stage Workflow

The lifecycle of a firewall policy cleanup is divided into five distinct, controlled stages:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Closed-Loop Firewall Hygiene Lifecycle                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Stage 1: Audit         Stage 2: Match & Find      Stage 3: Notify & Review │
│ ┌──────────────┐       ┌──────────────────────┐    ┌──────────────────────┐ │
│ │ Panorama API │──────▶│ Parse Rule Ticket ID │───▶│ Secure, SSO-Locked   │ │
│ │ 0-Hit Rules  │       │ ServiceNow API Query │    │ Review Link Email    │ │
│ └──────────────┘       └──────────────────────┘    └──────────┬───────────┘ │
│                                                               │             │
│                                                               ▼             │
│  Stage 5: Parallel Purge  Stage 4: Bulk Enforce         Owner Decisions     │
│ ┌──────────────────────┐  ┌────────────────────┐   ┌──────────────────────┐ │
│ │ 30-60 Day Monitor    │◀─│ Admin Dashboard    │◀──│ Exclude / Retain /   │ │
│ │ Concurrent Deletion  │  │ Single-Click Block │   │ Disable / Delete     │ │
│ └──────────────────────┘  └────────────────────┘   └──────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

* **Stage 1: Hit-Counter Audit:** Connects to the Panorama XML API, querying hit counters across all device groups to identify policies with zero traffic hits in the last 365 days.
* **Stage 2: Ownership Matching:** Parses the rule name to extract the original ServiceNow RITM/SCTASK ID and queries ServiceNow to resolve the active email of the request owner.
* **Stage 3: Secure Owner Review:** Sends a secure, unique email link to the owner, consolidating all their stale rules onto a single workspace. The owner logs in and selects: *Disable/Delete*, *Retain*, or *Exclude*.
* **Stage 4: Bulk Enforcement:** Stages owner submissions in the SQLite database. Administrators review the justifications and disable approved rules in a single bulk API transaction.
* **Stage 5: Parallel Purge & Tagging:** Spawns multi-threaded background workers to execute deletions concurrently. Rules marked for retention are programmatically tagged to bypass future audits.

---

## 5. ServiceNow Integration

To automate owner discovery, the engine integrates with the **ServiceNow REST API** at `https://enterprise.service-now.com` (authenticating with a service account `<SERVICENOW_PASSWORD_SCRUBBED>`). 

When a 0-hit rule is identified, the script programmatically resolves the original ticket owner. By mapping the firewall rule name directly to active directory records, the system identifies the exact engineer (e.g., resolving internal IDs to `security-ops@enterprise.com`), ensuring that every cleanup task is routed to the correct human reviewer.

---

## 6. Panorama API Automation

All interactions with Palo Alto Panorama are executed programmatically via the **Palo Alto Panorama XML API** at `<PROD_PANORAMA_IP>`:
* **Active Queries:** Pulls complete security policy configurations, device groups, and hit counters.
* **Controlled Disabling:** Spawns API requests to toggle the `disabled` state of approved rules.
* **Persistent Tagging:** Writes custom exclusion tags (like `Retain` or `Do-not-delete`) directly to the policy metadata, ensuring the rule is excluded from all future audit reports.

---

## 7. Safety Checks and Security Hardening

To protect production traffic and secure operational data, we implemented several safety gates:
* **SSO & User Auto-Provisioning:** The review portal integrates with Microsoft Entra ID (Azure AD) SSO, validating that only the authenticated owner can access their specific review portal.
* **The 30-to-60-Day cooling-off Period:** Rules are kept in a disabled state for 30 to 60 days. This blocks traffic but allows administrators to re-enable the rule in a single click if an unexpected application dependency arises.
* **Database & Thread Safety:** SQLite transaction locks protect data integrity, while strict payload size limits (`MAX_JSON_BYTES = 1024 * 1024`) and rate-limiting safeguard the server.

---

## 8. Dashboard Walkthrough

Below is a looping, high-fidelity demonstration showcasing **every single tab of the active application**. 

All sensitive corporate credentials and private IP topologies have been replaced with **realistic, high-fidelity demo data** (such as a generic `NL SECURITY` brand header, demo IPs, and masked form password inputs). This offers a clear, unredacted, and professional demonstration of the system:

![Automated Firewall Hygiene Pipeline Demo Walkthrough](./assets/demo_walkthrough.gif)

### Step-by-Step Tab & Pipeline Tour:

1. **Frame 1: Flow Tab (System Chart):** Displays the system workflow chart, illustrating how Python orchestration scripts pull 0-hit rules from Panorama, query ServiceNow, dispatch review links, and execute bulk changes.
2. **Frame 3: Overview Tab (Dashboard):** Loads the main executive dashboard, displaying total rules audited, pending reviews, active connection status to the Panorama management server, and global run metrics.
3. **Frame 4: Audit Tab (0-Hit Grid):** Displays the active rule hit-counter audit grid, showing rule names, resolved emails, and device groups rendered as realistic, mask-free table records.
4. **Frame 5: Encrypted Owner Email:** Displays the automated review notification sent to a resolved owner containing a secure, cryptographically-signed review link.
5. **Frame 6: Reviews Tab (Decision Portal):** Shows the individual owner review portal. It consolidates all rules owned by that user, providing interactive buttons to log choices: *Disable*, *Delete*, or *Retain* (requiring business justification).
6. **Frame 11: Settings Tab (Credentials Form):** The secure administrator settings panel populated with realistic configuration settings and masked password bullet fields (`••••••••`).
7. **Frame 12: Jobs Tab (Scheduler Logs):** Displays log outputs of the multi-threaded background queue executing Panorama syncs and ServiceNow queries asynchronously.

---

## 9. Lessons Learned

Through implementing and running this system, we gathered several valuable operational insights:
* **Grounded Language Beats Sales Pitching:** Technical documentation and dashboards are far more effective when they use clear, precise, and realistic labels rather than exaggerated placeholders.
* **Automated Sanitization is Critical:** Programmatic regex sanitization of operational variables (IPs, keys, and domains) is essential to prevent accidental exposure of internal infrastructure details in public logs.
* **Masking is Cleaner than Redaction Blocks:** Using realistic demo data and password masking characters (bullets) keeps the entire interface visible, maintaining the authentic look of the application while fully securing the data.

---

## 10. What I Would Improve Next

The next phase of our engineering roadmap involves a **fully autonomous monthly integration**:
* **Automated ServiceNow Trigger:** A recurring monthly scheduled job will be configured directly in ServiceNow.
* **Autonomous Pipeline Execution:** This job will automatically trigger our Python orchestrator, kicking off the hit-counter audit across all firewalls.
* **End-to-End Flow:** The pipeline will run completely unattended—extracting tickets, discovering owners, emailing secure review workspaces, compiling decisions, and staging bulk disable changes for administrator review.
