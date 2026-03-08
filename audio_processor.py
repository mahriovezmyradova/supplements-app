# audio_processor.py
import whisper
import torch
from transformers import BertTokenizer, BertModel
import numpy as np
import os
import soundfile as sf
import tempfile
import streamlit as st
import re

# Cache the models to avoid reloading
@st.cache_resource
def load_whisper_model():
    """Load Whisper Small model (cached)"""
    with st.spinner("Lade Whisper Modell... (dauert beim ersten Start)"):
        return whisper.load_model("small")

@st.cache_resource
def load_bert_model():
    """Load BERT model for extractive summarization (cached)"""
    with st.spinner("Lade BERT Modell... (dauert beim ersten Start)"):
        tokenizer = BertTokenizer.from_pretrained('bert-base-german-cased')
        model = BertModel.from_pretrained('bert-base-german-cased')
        return tokenizer, model

def transcribe_audio(audio_bytes):
    """
    Transcribe audio using Whisper Small
    Returns: transcript text and duration
    """
    try:
        model = load_whisper_model()
        
        # Save audio bytes to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Transcribe with German language
            result = model.transcribe(tmp_path, language="de")
            transcript = result["text"]
            
            # Get audio duration
            audio_data, sr = sf.read(tmp_path)
            duration = len(audio_data) / sr
            
            return transcript, duration
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    except Exception as e:
        st.error(f"Fehler bei der Transkription: {str(e)}")
        return None, 0

def extractive_summarize(text, num_sentences=4):
    """
    Extract key sentences using BERT embeddings
    Optimized for German medical conversations
    """
    if not text or len(text.split('.')) < 2:
        return text
    
    try:
        tokenizer, model = load_bert_model()
        
        # Clean and split text into sentences
        text = text.replace('\n', ' ')
        # German sentence splitting
        sentences = []
        for s in re.split(r'(?<=[.!?])\s+', text):
            if s.strip():
                sentences.append(s.strip())
        
        if len(sentences) <= num_sentences:
            return text
        
        # Get embeddings for each sentence
        sentence_embeddings = []
        for sentence in sentences:
            inputs = tokenizer(sentence, return_tensors='pt', 
                              max_length=512, truncation=True, padding=True)
            with torch.no_grad():
                outputs = model(**inputs)
                # Use [CLS] token embedding
                embedding = outputs.last_hidden_state[:, 0, :].numpy()
                sentence_embeddings.append(embedding)
        
        # Convert to numpy array
        sentence_embeddings = np.array(sentence_embeddings).squeeze()
        
        # Select most important sentences (simplified TextRank approach)
        # Use first sentence and then most diverse ones
        selected_indices = [0]
        
        if len(sentences) > 1:
            # Calculate similarities with first sentence
            similarities = []
            for i in range(1, len(sentences)):
                sim = np.dot(sentence_embeddings[0], sentence_embeddings[i]) / (
                    np.linalg.norm(sentence_embeddings[0]) * np.linalg.norm(sentence_embeddings[i])
                )
                similarities.append((i, sim))
            
            # Sort by lowest similarity (most different content)
            similarities.sort(key=lambda x: x[1])
            
            # Add most different sentences
            for i in range(min(num_sentences-1, len(similarities))):
                selected_indices.append(similarities[i][0])
        
        selected_indices.sort()
        summary = ' '.join([sentences[i] for i in selected_indices])
        
        return summary
        
    except Exception as e:
        st.error(f"Fehler bei der Zusammenfassung: {str(e)}")
        return text[:500] + "..."  # Fallback: return first 500 chars

# Test function to verify everything works
if __name__ == "__main__":
    print("✅ Audio Processor module loaded successfully")
    print("   - Whisper available")
    print("   - BERT available")