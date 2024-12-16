#!/usr/bin/env python3
"""Setup script for Gonzo installation."""
import subprocess
import sys
import os

def install_requirements():
    print("\n🔧 Installing Python dependencies...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def install_nltk_data():
    print("\n📚 Downloading required NLTK data...")
    import nltk
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('brown')

def setup_textblob():
    print("\n🔄 Setting up TextBlob...")
    import textblob
    textblob.download_corpora()

def main():
    print("🚀 Starting Gonzo setup...\n")
    
    try:
        install_requirements()
        install_nltk_data()
        setup_textblob()
        
        print("\n✅ Setup complete! You can now run Gonzo using:")
        print("python test_gonzo_live.py")
        
    except Exception as e:
        print(f"\n❌ Error during setup: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()