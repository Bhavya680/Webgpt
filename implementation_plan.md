# Implementation Plan: Running the LLM on Intel Graphics

The original `load_model.py` script was designed to run the model natively on NVIDIA GPUs (using 4-bit `bitsandbytes` processing). However, based on the Task Manager screenshot you provided, your machine has different hardware. 

## Hardware Analysis
1. **GPU:** You have an **Intel(R) Graphics** integrated GPU, and an **NPU (AI Boost)**. You do not have an NVIDIA GPU, which means CUDA and `bitsandbytes` (used for 4-bit compression) are not compatible with your hardware.
2. **RAM Constraint:** Your system memory is at **13.5 / 15.4 GB (88% utilization)**. You only have ~1.9 GB of free physical RAM. Loading the Gemma-2B model + LoRA adapter requires at least ~5 GB of RAM.

## User Review Required
> [!CAUTION]
> Because you only have ~1.9 GB of free RAM, loading the model locally via Python will rely heavily on **Windows Virtual Memory (Disk Swap)**. This may cause your computer to become temporarily unresponsive or run very slowly while loading the model. 
> 
> **Are you able to close heavy background applications (like browsers or Discord) to free up memory before we try to run the model?**

## Proposed Changes

We cannot use standard PyTorch CUDA for an Intel GPU. Instead, we can try using **PyTorch with DirectML** which is designed by Microsoft to accelerate AI workloads on any DirectX 12 capable GPU (including your Intel Graphics).

### Phase 1: Environment Modifications
- Install `torch-directml`, a specialized version of PyTorch for Windows/Intel GPUs.
- Confirm that DirectML successfully detects the Intel Graphics hardware.

### [ai_engine]

#### [MODIFY] [load_model.py](file:///c:/Users/Urvi/OneDrive/Desktop/Webgpt/scripts/load_model.py)
We will rewrite the loading script to:
1. Detect and load the `torch_directml` backend instead of CUDA.
2. Load the standard `google/gemma-2b-it` base model in `bfloat16` precision (the lowest memory footprint available for DirectML without NVIDIA-specific quantizations).
3. Map the model entirely to the `dml` (DirectML) device so it runs on the Intel Graphics module.
4. Merge your `my-adapter` LoRA safely into the base model.

## Open Questions

> [!IMPORTANT]
> If DirectML runs out of memory (OOM Crash) due to the limited RAM, the **Alternative Approach** would be to use a tool called `llama.cpp` using the **Vulkan** backend, which is highly optimized for Intel GPUs and extreme low-RAM environments. 
>
> **Do you approve of proceeding with the PyTorch DirectML approach first?**
