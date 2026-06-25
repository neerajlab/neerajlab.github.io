---
title: "Automated Firewall Hygiene System"
category: "Security Engineering"
tags: "Palo Alto, Panorama, Python, ServiceNow, Automation, Cybersecurity"
cover: "./assets/firewall_hygiene.png"
read_time: "10 min read"
description: "A 5-stage firewall hygiene workflow that identifies stale rules, resolves ownership through ServiceNow, supports owner review, and stages controlled cleanup through Palo Alto Panorama APIs."
date: "June 26, 2026"
---

# Automated Firewall Hygiene System
*A practical 5-stage workflow for identifying stale firewall rules, resolving ownership, collecting review decisions, and safely staging cleanup actions.*

## 1. Introduction

Managing firewall policies across an enterprise network requires balancing operational uptime with a strong security posture. Over years of operations, security rules inevitably accumulate. Rules created for temporary access, vendor testing, or legacy applications are often abandoned once they are no longer needed.

This post walks through the architecture of an **Automated Firewall Hygiene System** — a 5-stage workflow that connects firewall rule usage data, ownership lookup, human review, and controlled enforcement, while reducing the risk of operational impact.

I built this workflow to make stale rule reviews more consistent, reduce manual tracking, and keep enforcement actions behind clear approval gates.

## 2. The Problem: Stale Firewall Rules

As enterprise networks grow, firewall rule bloat becomes increasingly common. Obsolete rules present several key challenges:
* **Expanded Attack Surface:** Every active rule that is no longer required can expand the possible paths for unauthorized access.
* **Compliance & Audit Debt:** Bloated security policies complicate cybersecurity compliance audits, making it difficult to justify active rules.
* **Operational Complexity:** Large rulebases become harder to review, troubleshoot, and safely change.
* **Performance Overhead:** Large, unoptimized policy tables can add operational overhead and may affect performance depending on platform and policy structure.

## 3. Why Manual Cleanup Is Risky

Manually identifying and cleaning up stale rules is highly inefficient and introduces significant operational risks:
* **Lack of Context:** A rule name does not tell a security administrator who owns the application today, or if the underlying servers have been decommissioned.
* **Fear of Breaking the Network:** Without verified ownership and usage data, security teams are hesitant to delete policies, fearing they might disrupt a critical business service.
* **Spreadsheet Fragmentation:** Exporting rule tables to spreadsheets and emailing them to application owners leads to ignored threads, outdated tracking, and lost decisions.

To solve this, I designed the workflow to replace spreadsheet-driven reviews with a programmatic, human-in-the-loop orchestration pipeline.

## 4. System Architecture

The system has two main components designed to operate with minimal external dependencies:

1. **Automation Orchestrator:** A Python service that queries firewall data, parses rule metadata, resolves ownership, and stages enforcement actions.
2. **Review Dashboard:** A lightweight web portal backed by SQLite for reviewer sessions, owner decisions, admin review, and audit state tracking.

## 5. The 5-Stage Workflow

The lifecycle of a firewall policy cleanup is divided into five distinct, controlled stages:

**Audit** &rarr; **Match Owner** &rarr; **Notify & Review** &rarr; **Admin Review & Enforce** &rarr; **Monitor & Remove**

* **Stage 1: Hit-Counter Audit:** Connects to the Panorama XML API, querying hit counters across all device groups to identify policies with zero traffic hits in the last 365 days.
* **Stage 2: Ownership Matching:** Parses the rule name to extract the original ServiceNow ticket ID and queries ServiceNow to resolve the active email of the request owner.
* **Stage 3: Secure Owner Review:** Sends a secure, unique email link to the owner, consolidating all their stale rules onto a single workspace. The owner logs in and selects a review decision such as disable, retain, or exclude, with justification where required.
* **Stage 4: Admin Review & Enforcement:** Stages owner submissions in the SQLite database. Administrators review the justifications and disable approved rules in a single bulk API transaction.
* **Stage 5: Monitor, Remove, and Tag:** Keeps disabled rules in a cooling-off period to monitor for unexpected traffic. Rules that complete the cooling-off period are approved for removal using background workers that process cleanup actions in a controlled queue. Rules marked for retention are programmatically tagged so they are handled as approved exceptions in future audits.

## 6. ServiceNow Ownership Resolution

The workflow uses ServiceNow REST APIs to resolve ownership metadata from the original request or task associated with a firewall rule.

When a stale rule is identified, the system extracts the request reference from the rule metadata, queries the ticket record, and maps it to the current owner or support contact. This allows review requests to be routed to the right person instead of relying on manual spreadsheets or outdated ownership notes.

## 7. Panorama API Automation

All firewall policy interactions are handled through Palo Alto Panorama APIs. The automation queries policy configuration, device groups, and rule usage data, then stages approved changes for administrator review.

* **Active Queries:** Pulls complete security policy configurations, device groups, and hit counters.
* **Controlled Disabling:** Updates the disabled state only for rules approved through the review workflow.
* **Persistent Tagging:** Writes custom review tags, such as Retain or Do-not-delete, directly to the policy metadata, ensuring the rule is excluded from all future audit reports.

## 8. Safety Checks and Approval Gates

The most important part of the system is not deletion — it is control. The workflow includes several safety gates before any firewall change is applied:

* **SSO-based Access:** Reviewers only see rules assigned to them.
* **Human-in-the-Loop Approval:** No changes are made without owner review and justification.
* **Admin Review:** A final verification gate before any bulk disable or cleanup actions are committed.
* **30-to-60-Day Cooling-Off Period:** Rules are kept in a disabled state first, giving teams time to catch unexpected dependencies before permanent removal.
* **Operational Controls:** Logging, transaction controls, and rate limiting to protect the review portal and preserve audit history.

## 9. Dashboard Walkthrough

The demo below walks through the main dashboard views and review workflow.

All sensitive values, internal hostnames, IP addresses, credentials, and topology details have been replaced with sanitized demo data.

![Automated Firewall Hygiene Pipeline Demo Walkthrough](./assets/demo_walkthrough.gif)

The walkthrough covers:
* System flow and pipeline stages
* Audit results for stale firewall rules
* Owner resolution and review notifications
* Reviewer decision workflow
* Admin dashboard, job logs, and staged enforcement actions

## 10. Lessons Learned

Building the workflow reinforced a few important lessons:

* **Ownership data matters more than rule data.** Finding unused rules is only the first step; identifying the right owner is what makes cleanup possible.
* **Disable-before-delete is safer than direct deletion.** A cooling-off period gives teams time to catch unexpected dependencies before permanent removal.
* **Human review is still necessary.** Automation can collect data, route decisions, and stage actions, but production firewall changes still need clear approval gates.
* **Audit history is part of the product.** Every decision, justification, and enforcement action should be logged so the process can stand up to future review.
* **Simple tooling is easier to operate.** A lightweight dashboard with clear stages can be more useful than a complex platform that is hard to maintain.

## 11. What I Would Improve Next

The next improvement would be a scheduled monthly workflow that automatically starts the audit cycle while keeping enforcement actions behind review and approval gates.

Planned improvements:
* Trigger the audit from a scheduled ServiceNow or orchestration job.
* Automatically collect 0-hit rule candidates from Panorama.
* Resolve ownership and send review requests without manual spreadsheet handling.
* Track owner decisions and reminders in the dashboard.
* Keep disable and delete actions behind administrator approval.
* Add reporting for cleanup progress, retained rules, and audit exceptions.
