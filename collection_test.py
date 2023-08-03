from model.transcript_filler import create_whisper_transcript_filler, create_ytdlp_transcript_filler

# filler = create_ytdlp_transcript_filler(db_name="youtube", collection_name="atom")
# filler.fill_missing_transcripts()

filler = create_whisper_transcript_filler(db_name="youtube", collection_name="atom")
filler.fill_missing_transcripts()
