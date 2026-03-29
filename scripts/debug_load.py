import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
try:
    bnb_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16, bnb_4bit_quant_type='nf4')
    print("Loading model...")
    model = AutoModelForCausalLM.from_pretrained('unsloth/gemma-2b-it-bnb-4bit', device_map='auto', quantization_config=bnb_config)
    print("Success!")
except Exception as e:
    print("FAILED:", e)

