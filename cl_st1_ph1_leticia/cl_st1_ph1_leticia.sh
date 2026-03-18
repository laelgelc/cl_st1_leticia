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





