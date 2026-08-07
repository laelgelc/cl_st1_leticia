# Expanding POS Tags for Conversational AI Analysis

## Me
Hi! How are you doing, AI Assistant?

Please consider the attached English tagset of TreeTagger part-of-speech (POS) tagger.

This research looks at whether AI can simulate human identities in conversational
interaction.

Currently, the following features were selected for analysis: `"NN", "NP", "VB", "JJ"`. Those are prefixes that select the tags that begin with those prefixes. This selection restricted features that are relevant in conversational interaction, such as interjections, for instance.

If you were the supervisor of the researcher running this study, which tags would you ask to include?

## AI Assistant
Hi! I’m doing well, thank you.

As a supervisor, I would ask the researcher to broaden the feature set beyond lexical-content categories like nouns, verbs, adjectives, and proper nouns. For conversational identity simulation, many of the most revealing signals are **interactional, stance-related, deictic, and discourse-structuring** features.

The current prefixes:

```plain text
NN, NP, VB, JJ
```


capture mainly:

- common nouns
- proper nouns
- verbs
- adjectives

Those are useful, but they miss several POS categories that are highly relevant to conversational interaction.

## Tags I would ask to include

### Strongly recommended

| Tag / prefix | Category | Why include it |
|---|---|---|
| `UH` | Interjection | Captures conversational markers such as “oh”, “uh”, “yes”, “wow”, “hmm”; highly relevant to interactional style |
| `PP` | Personal pronoun | Important for identity, stance, self-reference, address, and interpersonal orientation |
| `PP$` | Possessive pronoun | Captures forms like “my”, “your”, “our”; useful for ownership, affiliation, and relational framing |
| `RB` | Adverb | Captures stance and intensity: “really”, “just”, “maybe”, “actually”, “probably” |
| `MD` | Modal | Important for politeness, uncertainty, obligation, and agency: “can”, “could”, “should”, “would” |
| `WP` | Wh-pronoun | Relevant for question formation and conversational engagement |
| `WRB` | Wh-adverb | Captures questions like “why”, “how”, “when”, “where” |
| `WDT` | Wh-determiner | Adds coverage for interrogative structures such as “which” and “what” |

## I would especially prioritize these

If the researcher needs a compact extension, I would recommend:

```plain text
UH, PP, PP$, RB, MD, WP, WRB, WDT
```


This would add:

- interjections
- personal and possessive pronouns
- adverbs and stance markers
- modals
- question-related forms

These are central to conversational behavior and identity performance.

## Additional useful tags

Depending on the study design, I would also consider:

| Tag / prefix | Category | Why it may matter |
|---|---|---|
| `CC` | Coordinating conjunction | Conversational flow, clause linking, additive style |
| `IN` | Preposition/subordinating conjunction | Complex clause structure, elaboration style |
| `DT` | Determiner | Referential style, specificity, noun-phrase construction |
| `EX` | Existential there | Conversational constructions like “there is”, “there are” |
| `TO` | “to” | Infinitival constructions, planning, intention |
| `RP` | Particle | Phrasal verbs and colloquial patterns |
| `PDT` | Predeterminer | Less frequent, but may capture emphasis: “all the”, “both the” |

## My supervisory recommendation

I would advise replacing the current narrow feature set with something like:

```plain text
NN, NP, VB, JJ, UH, PP, PP$, RB, MD, WP, WRB, WDT
```


Or, if the study aims to model conversational identity more comprehensively:

```plain text
NN, NP, VB, JJ, UH, PP, PP$, RB, MD, WP, WRB, WDT, CC, IN, DT, EX, TO, RP
```


## Rationale

For a study on whether AI can simulate human identities in conversation, I would argue that the most important additions are not more content-word categories, but **interactional and grammatical markers**:

- **Interjections** show responsiveness and conversational naturalness.
- **Pronouns** reveal self-positioning, address, affiliation, and identity claims.
- **Modals** show politeness, hesitation, authority, and uncertainty.
- **Adverbs** often encode stance, emphasis, mitigation, and affect.
- **Wh-tags** capture questioning behavior and interactional engagement.

So my main recommendation would be: **include `UH`, pronouns, modals, adverbs, and wh-categories at minimum**.

## Me
Please refactor this selection according to your recommendations.

## AI Assistant
Refactored selection:

```python
# POS tags to keep: content words + conversational/interactional markers
# Includes nouns, proper nouns, verbs, adjectives, interjections,
# pronouns, possessive pronouns, adverbs, modals, and wh-categories.
VALID_TAG_PREFIXES = (
    "NN",   # Nouns
    "NP",   # Proper nouns
    "VB",   # Verbs
    "JJ",   # Adjectives
    "UH",   # Interjections
    "PP",   # Personal pronouns
    "PP$",  # Possessive pronouns
    "RB",   # Adverbs
    "MD",   # Modals
    "WP",   # Wh-pronouns
    "WRB",  # Wh-adverbs
    "WDT",  # Wh-determiners
)
```


## Me
Question: Wouldn't "PP" include "PP$"?

## AI Assistant
Yes — **if your filtering uses prefix matching**, then `"PP"` already includes `"PP$"`.

For example, if the logic is equivalent to:

```python
tag.startswith(VALID_TAG_PREFIXES)
```


then:

```python
"PP$".startswith("PP")  # True
```


So in that case, listing both `"PP"` and `"PP$"` is redundant.

You can simplify it to:

```python
VALID_TAG_PREFIXES = (
    "NN",   # Nouns
    "NP",   # Proper nouns
    "VB",   # Verbs
    "JJ",   # Adjectives
    "UH",   # Interjections
    "PP",   # Personal and possessive pronouns
    "RB",   # Adverbs
    "MD",   # Modals
    "WP",   # Wh-pronouns, including possessive wh-pronouns
    "WRB",  # Wh-adverbs
    "WDT",  # Wh-determiners
)
```


The same applies to `"WP"` and `"WP$"`: with prefix matching, `"WP"` also includes `"WP$"`.

So the cleaner recommendation is:

```python
VALID_TAG_PREFIXES = ("NN", "NP", "VB", "JJ", "UH", "PP", "RB", "MD", "WP", "WRB", "WDT")
```


This keeps the intended coverage while avoiding redundant prefixes.
