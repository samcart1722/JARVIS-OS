# JARVIS-OS Ubiquitous Language
Version: 1.0
Status: Draft
Author: JARVIS-OS Team

---

# 1. Purpose

This document defines the official ubiquitous language of JARVIS-OS.

Every cognitive domain, API, service, model, test, and document must use the terminology defined here.

The objective is to eliminate ambiguity across the entire project.

Whenever a concept already exists in this document, new names must not be invented.

---

# 2. Core Principles

The ubiquitous language follows these principles.

- One concept has one name.
- One name has one meaning.
- Synonyms are not allowed.
- Domain terminology is preferred over technical terminology.
- Code, documentation and conversations must use the same vocabulary.

---

# 3. Cognitive Concepts

## Agent

The autonomous cognitive entity that performs reasoning.

In JARVIS-OS the primary agent is JARVIS itself.

---

## User

The human interacting with the system.

The user provides goals, requests, information and feedback.

---

## Conversation

A chronological sequence of interactions between the user and JARVIS.

A conversation contains messages and contextual metadata.

A conversation is not memory.

---

## Message

A single communication exchanged between participants.

Messages may originate from:

- User
- Assistant
- System
- Tool

---

## Intent

The interpreted purpose behind a user's message.

Intent represents what the user wants.

Examples:

- Ask Question
- Solve Problem
- Execute Task
- Search Information
- Explain Concept

Intent is inferred.

Intent is never persisted as memory.

---

## Goal

A desired outcome selected after intent recognition.

Goals guide reasoning.

Examples:

- Answer a question
- Produce a report
- Schedule a reminder
- Search documentation

Goals may generate plans.

---

## Task

A single executable cognitive action.

Tasks are atomic.

Examples:

- Retrieve memories
- Search knowledge
- Call a tool
- Summarize text

Tasks compose plans.

---

## Plan

An ordered collection of tasks.

Plans describe how a goal will be achieved.

Plans do not execute themselves.

---

# 4. Memory Concepts

## Memory

A stored experience that may become useful in future interactions.

Memory is persistent.

Memory is searchable.

Memory is ranked before retrieval.

---

## Memory Entry

A single stored memory.

Contains:

- content
- metadata
- classification
- timestamps

---

## Memory Recall

The process of retrieving relevant memories.

Memory recall never modifies stored memories.

---

## Memory Ranking

The process of ordering retrieved memories according to relevance.

Ranking occurs before reasoning.

---

# 5. Knowledge Concepts

## Knowledge

Verified factual information.

Knowledge differs from memory.

Knowledge represents facts.

Memory represents experiences.

---

## Knowledge Source

A provider of factual information.

Examples:

- Documentation
- Database
- API
- Search Index

---

# 6. Reasoning Concepts

## Reasoning

The cognitive process responsible for deciding what should happen next.

Reasoning coordinates domains.

Reasoning does not execute external actions.

---

## Thought

An internal reasoning step.

Thoughts are transient.

Thoughts are not responses.

Thoughts are not memories.

Thoughts may produce plans.

---

## Decision

A selected course of action.

Decisions are produced by reasoning.

Examples:

- Use memory
- Call a tool
- Ask the LLM
- Request clarification

---

# 7. Context Concepts

## Context

The complete information package required for reasoning.

Context is assembled from multiple sources.

Context is temporary.

---

## Cognitive Context

The structured object produced by the Context domain.

It may contain:

- conversation
- memories
- knowledge
- goals
- plans
- tool results

---

# 8. Prompt Concepts

## Prompt

The formatted instruction sent to a language model.

A prompt is generated from context.

Prompts are disposable.

Prompts are never considered memory.

---

# 9. Tool Concepts

## Tool

An external capability available to JARVIS.

Examples:

- File System
- Browser
- Python
- Database
- Automation

---

## Tool Call

A single execution of a tool.

Tool calls produce results.

Tool calls are observable.

---

## Tool Result

The structured output returned by a tool.

Reasoning consumes tool results.

---

# 10. Reflection Concepts

## Reflection

The evaluation of an already generated response.

Reflection answers questions such as:

- Is it correct?
- Is it complete?
- Is it consistent?
- Is another reasoning cycle required?

Reflection occurs after reasoning.

---

## Confidence

The estimated reliability of a response.

Confidence is an evaluation.

Confidence is not certainty.

---

# 11. Learning Concepts

## Learning

The process of improving future behavior using completed interactions.

Learning determines:

- what becomes memory
- what should be ignored
- what patterns emerge

---

## Experience

A completed interaction that may become memory.

Not every experience becomes memory.

---

# 12. Architectural Concepts

## Cognitive Domain

An independent module responsible for one cognitive capability.

Examples:

- Memory
- Reasoning
- Context
- Learning
- Reflection

---

## Pipeline

A deterministic sequence of processing stages.

Each stage has one responsibility.

---

## Orchestration

The coordination of multiple cognitive domains.

Orchestration belongs to the Reasoning Engine.

---

# 13. Reserved Terms

The following words are reserved and must not be redefined elsewhere.

- Agent
- User
- Conversation
- Message
- Intent
- Goal
- Task
- Plan
- Memory
- Knowledge
- Context
- Prompt
- Tool
- Reflection
- Learning
- Decision
- Pipeline
- Reasoning

---

# 14. Naming Rules

When introducing new concepts:

- Prefer nouns over verbs.
- Avoid abbreviations.
- Avoid synonyms.
- Use singular names.
- Keep terminology stable over time.

Examples:

Correct:

Memory

Incorrect:

MemoryObject

StoredMemoryItem

PersistentKnowledgeMemory

---

# 15. Final Statement

The ubiquitous language is part of the architecture.

Changing terminology changes the architecture.

Every contributor to JARVIS-OS is expected to use the vocabulary defined in this document consistently across code, documentation and discussions.