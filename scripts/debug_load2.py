import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
try:
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained('unsloth/gemma-2b-it-bnb-4bit', device_map='auto')
    print("Success!")
except Exception as e:
    print("FAILED:", e)

