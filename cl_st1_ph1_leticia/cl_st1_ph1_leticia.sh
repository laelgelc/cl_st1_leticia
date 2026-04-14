python 01_import_bnc2014sp.py

python 02_summarise_turns.py \
    --model gpt-5.1 \
    --workers 4 \
    #--test 10

python 03_build_prompts_profiled.py

python 03_build_prompts_unprofiled.py

python 04_generate_human.py

python 04_generate_gpt.py \
    --input corpus/04_prompt_profiled \
    --output corpus/05_profiled_gpt \
    --file-index file_index.txt \
    --model gpt-5.1 \
    --workers 4 \
    #--test 10

python 04_generate_gpt.py \
    --input corpus/04_prompt_unprofiled \
    --output corpus/05_unprofiled_gpt \
    --file-index file_index.txt \
    --model gpt-5.1 \
    --workers 4 \
    #--test 10

python tag.py
# Output: corpus/07_tagged

python keylemmas.py \
    --input corpus/07_tagged \
    --output corpus/08_keylemmas \
    --cutoff 3

python select_kws_stratified.py \
    --ceiling 250 \
    --human-weight 2 \
    --max-total 1200
# Output: corpus/09_kw_selected

# Case 1 (Issues: "NP" tag is for proper nouns; "VV" and "AJ" tags do not exist)
# POS tags to keep: nouns, main verbs, adjectives (NO ADVERBS)
#VALID_TAG_PREFIXES = ("NN", "NP", "VV", "AJ")
"
=== Keyword Quotas ===
human           → 500 keywords (max)
profiled_gpt    → 250 keywords (max)
unprofiled_gpt  → 250 keywords (max)
=======================

human           → selected 16/500 keywords
profiled_gpt    → selected 18/250 keywords
unprofiled_gpt  → selected 14/250 keywords

Total consolidated keywords (incl. duplicates): 48
Unique keywords (used downstream): 38
Duplicates removed later: 10

Final unique keywords written: 38
"

# Case 2 (Included proper nouns; Corrected the errors)
# POS tags to keep: nouns, main verbs, adjectives (NO ADVERBS)
#VALID_TAG_PREFIXES = ("NN", "NP", "VB", "JJ")
"
=== Keyword Quotas ===
human           → 500 keywords (max)
profiled_gpt    → 250 keywords (max)
unprofiled_gpt  → 250 keywords (max)
=======================

human           → selected 34/500 keywords
profiled_gpt    → selected 54/250 keywords
unprofiled_gpt  → selected 45/250 keywords

Total consolidated keywords (incl. duplicates): 133
Unique keywords (used downstream): 106
Duplicates removed later: 27

Final unique keywords written: 106
"

# Excluding "em", "er", "erm", "um" (exclamations from the human corpus)
"
=== Keyword Quotas ===
human           → 500 keywords (max)
profiled_gpt    → 250 keywords (max)
unprofiled_gpt  → 250 keywords (max)
=======================

human           → selected 30/500 keywords
profiled_gpt    → selected 54/250 keywords
unprofiled_gpt  → selected 45/250 keywords

Total consolidated keywords (incl. duplicates): 129
Unique keywords (used downstream): 102
Duplicates removed later: 27

Final unique keywords written: 102
"

rm -rf columns columns_clean
python columns.py
# Output: columns, columns_clean, file_ids.txt, index_keywords.txt

python merge_columns.py
# Output: sas/counts.txt

python sas_formats.py
# Output: sas/word_labels_format.sas, etc

## RUN SAS
## Rogerio Yamada's account

python factor_lists.py
# Output: factors

python corpus_size.py
# Output: corpus_size/corpus_size.tsv

cd latex_boxplots
# Builds boxplots for factor analysis:
python latex_boxplots.py
# Output: latex_boxplots/slides
cd ..

python latex_anova_table.py
# Output: latex_tables

python examples.py
# Output: examples (LaTeX format)

# Sanity check on the scores:
python score_details.py
# Output: examples/score_details.txt

python examples_txt.py
# Output: examples_txt (plaintext format)

# Interpretation
# Build prompts:
python interpretation_prompts.py
# Output: interpretation/input

# Submit prompts:
python generate_interpretation_gpt.py \
    --input interpretation/input \
    --output interpretation/output \
    --model gpt-5.1 \
    --workers 4
# Output: interpretation/output