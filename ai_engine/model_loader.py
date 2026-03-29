import os
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig, pipeline
from peft import PeftModel

_pipeline = None

def get_custom_pipeline():
    global _pipeline
    
    if _pipeline is not None:
        return _pipeline
        
    USE_FINETUNED = os.getenv('USE_FINETUNED', 'False') == 'True'
    
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_quant_type='nf4'
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        'unsloth/gemma-2b-it-bnb-4bit',
        device_map='auto'
    )
    
    if USE_FINETUNED:
        model = PeftModel.from_pretrained(model, './local_storage/finetuning/my_adapter/')
        
    tokenizer = AutoTokenizer.from_pretrained('./local_storage/finetuning/my_adapter/')
    
    _pipeline = pipeline('text-generation', model=model, tokenizer=tokenizer)
    return _pipeline

def is_model_loaded() -> bool:
    return _pipeline is not None
