# Corpus Linguistics - Study 1 - Leticia

## Phase 1 - Oral presentation at IVACS 2026

### Overview

This project investigates how social identities are represented in conversation by comparing human interaction with AI-generated dialog. It is motivated by the question of whether AI can simulate human identities in ways that go beyond surface-level role performance and instead reflect broader discourse patterns and language-use choices.

While recent studies suggest that large language models can imitate social roles in conversation, this research focuses more specifically on how such identity simulations are realised linguistically. To address this, the study adopts a variationist, corpus-based approach centered on language use in spoken interaction.

The project draws on spoken corpus data to examine conversational structure, speaker participation, and recurring linguistic patterns that may distinguish human and AI-generated dialog. In this phase, the work is oriented toward preparing data and analytical resources for the study and for the oral presentation at IVACS 2026.

### Corpus Download

It was believed that the data source to be used was the [British National Corpus (BNC) 1994](corpus/bnc_archive/bnc_1994/bnc_1994.md) but it was clarified that the correct one was the [British National Corpus (BNC) 2014](https://cass.lancs.ac.uk/bnc2014/).

This task involves downloading the [BNC 2014 Spoken](http://corpora.lancs.ac.uk/bnc2014/):

- [Sign up for access](http://corpora.lancs.ac.uk/bnc2014/signup.php)

### Methodology

The project uses the BNC 2014 Spoken corpus as the source of naturally occurring human conversation. The accompanying Jupyter notebook documents the planning and corpus-building process, including the identification of speakers, top talkers, conversation sizes, and the preparation of human and GPT-generated turns.

The corpus is built around comparable conversational turns organised into three sub-corpora:

1. **human**: original human turns extracted from the BNC 2014 Spoken conversations.
2. **profiled_gpt**: GPT-generated turns produced with access to the socio-demographic profile of the original speaker being simulated.
3. **unprofiled_gpt**: GPT-generated turns produced without socio-demographic profile information, using only minimal speaker identification.

The workflow is as follows:

1. Parse BNC 2014 Spoken XML files and extract conversation metadata, speaker metadata, and utterance-level data.
2. Identify the most frequent speaker in each conversation as the target speaker for replacement/simulation.
3. Segment conversations into manageable conversational contexts for prompt construction.
4. Summarise the target human turns to guide controlled GPT generation.
5. Build two prompt sets:
   - a profiled condition, where socio-demographic speaker information is included;
   - an unprofiled condition, where such information is withheld.
6. Generate the corresponding GPT turns for both conditions.
7. Compile the final study corpus into the three sub-corpora: `human`, `profiled_gpt`, and `unprofiled_gpt`.
8. Tag, lemmatise, and select keywords for downstream corpus-linguistic and statistical analysis.

This design supports direct comparison between original human conversation and two forms of AI-generated dialog, allowing the study to examine whether access to speaker profile information affects linguistic patterning in simulated conversational turns.

### Pipeline

The main corpus compilation steps are organised as sequential scripts:
```shell
python 01_import_bnc2014sp.py
python 02_summarise_turns.py
python 03_build_prompts_profiled.py
python 03_build_prompts_unprofiled.py
python 04_generate_human.py
python 04_generate_gpt.py
```

The resulting corpus contains the balanced sample of selected conversation turns, with `1705` conversation turns per sub-corpus and `5115` conversation turns in total.

The Lexical Multi-dimensional Analysis (LMDA) was processed according to the corresponding procedures.

#### POS tag selection for keyword features

The valid tag prefixes used in keyword selection were defined to balance lexical content with features that are especially relevant to conversational interaction. An initial narrow selection focused on nouns, proper nouns, verbs, and adjectives. This was later broadened because identity simulation in dialogue is also reflected through interactional, stance-related, and discourse-structuring forms.

The final selection includes:

- `NN`: nouns
- `NP`: proper nouns
- `VB`: verbs
- `JJ`: adjectives
- `UH`: interjections
- `PP`: personal and possessive pronouns
- `RB`: adverbs
- `MD`: modals
- `WP`: wh-pronouns and possessive wh-pronouns
- `WRB`: wh-adverbs
- `WDT`: wh-determiners
- `CD`: coordinating conjunctions
- `IN`: prepositions

This expanded set captures not only referential and descriptive vocabulary, but also forms associated with stance, address, politeness, hesitation, questioning, emphasis, and conversational flow. Because prefix matching is used, broader prefixes such as `PP` and `WP` also cover their possessive subtypes.

