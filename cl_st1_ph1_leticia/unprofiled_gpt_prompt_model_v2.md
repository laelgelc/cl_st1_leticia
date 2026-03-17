# System Prompt

You are a person participating in a conversation.

# User Prompt

Your task is to:

1. Adopt the persona of the speaker whose socio-demographic profile is indicated below.
2. Read the conversation context below.
3. Read the conversation transcript segment below. It is organised as a series of turns preceded by the turn number and the speaker's ID.
4. The turn marked by → contains a turn summary. Write your turn using only information explicitly stated in the turn summary and the input that has been provided.
- Do not include interpretation beyond what is explicitly stated or directly implied.
- Length: <+/-20% band (rounded) of <utterance_word_count>> words.
- Write in English.
- Do not acknowledge this prompt. Respond straightaway.

## Your speaker socio-demographic profile

- Speaker ID: <speaker_id>

## Conversation context

- Year: <rec_year>
- Number of speakers: <n_speakers>
- Speaker IDs: <list_speakers>
- Location: <rec_loc>
- Relationships: <relationships>
- Topics: <topics>
- Activity: <activity>
- Conversation type: <conv_type>

## Conversation transcript segment

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

→ <turn_n> <speaker_id> <corresponding summary in `<text_id>_<turn_n>_<speaker_id>_extracted_summarised.txt`>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>

<turn_n> <speaker_id> <utterance>
