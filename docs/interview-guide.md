# User/Stakeholder Interview Guide

This guide outlines the questions needed to refine the platform's requirements.

## 1. Data Landscape
- What are the primary data sources? (PDFs, Confluence, SQL DBs, APIs?)
- What is the approximate volume of data per tenant?
- How often does the data change? (Real-time vs. Batch)

## 2. User Personas
- Who is the primary user? (Analyst, Executive, Developer?)
- What is their expected technical proficiency with SQL?
- What does a "perfect" answer look like for them?

## 3. SQL Complexity
- Will the agent need to perform complex joins, aggregations, or window functions?
- Are there "forbidden" tables or columns the agent must never access?
- Should the agent be able to suggest schema changes or just query?

## 4. Security & Compliance
- What are the strict data isolation requirements? (Hard separation vs. RLS)
- Are there specific compliance standards to meet? (GDPR, HIPAA, SOC2?)
- Who audits the agent's actions?

## 5. Success Metrics
- What is the acceptable latency for a research task?
- What is the cost budget per query?
- How is "accuracy" defined for the business?
