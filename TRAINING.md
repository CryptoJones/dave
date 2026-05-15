# Training Dave — Operator's Guide

How to launch a training run, read the metrics while it's going, decide when
to stop, and pick the best checkpoint. Audience: whoever is sitting in the
RunPod shell during a Dave fine-tune.

---

## Quick orientation

Dave is fine-tuned with **QLoRA** (Quantized Low-Rank Adaptation) on top of
**Llama-3.3-70B-Instruct**. The base weights are frozen at 4-bit precision;
we only learn a small set of "adapter" weights (LoRA, rank 16). This is what
lets a 70B model fit on a single 80GB GPU and finish in a few hours instead
of days.

The training run reads `data/shuffled_training.jsonl` (~11k prompt/completion
pairs) and writes adapter weights to `$DAVE_OUTPUT_DIR` (default
`./dave_adapter`).

---

## How long does training take?

**There is no single "done" point.** Most practitioners stop training when
the model stops improving on held-out data, not when it's "perfect." Three
distinct stopping signals matter:

1. **Loss plateaus.** If the training loss stops dropping meaningfully for
   ~50 consecutive optimizer steps, the model has extracted what it can
   from the data. Continuing past the plateau wastes compute.

2. **Eval loss starts going up while training loss keeps dropping.** This
   is **overfitting** — the model is memorizing training examples rather
   than learning the underlying pattern. Stop and roll back to an earlier
   checkpoint.

3. **Budget exhaustion.** Sometimes you just hit your compute or time
   budget. That's a legitimate reason to stop too.

### How that compares to other training regimes

| Stage | Typical duration | Why |
|---|---|---|
| Pretraining (Llama, GPT from scratch) | Weeks to months on hundreds of GPUs | Billions of tokens — learning language itself |
| Continued pretraining (domain adaptation) | Days | Hundreds of millions of tokens |
| **SFT / QLoRA (Dave)** | **1-3 epochs** | Small targeted dataset; teaching style and structure |
| DPO / RLHF (preference tuning) | 1 epoch | Aligning behavior to preferences |

### Dave's default: 1 epoch

`train_dave.py` defaults to **1 epoch**. With packing enabled
(`packing=True`) and `max_length=1024`, the 11k pairs collapse into roughly
280 optimizer steps. On A100 80GB that's ~3-4 hours wall-clock, ~$6 on
RunPod at $1.49/hr.

If you want more passes over the data, set `DAVE_EPOCHS=2` before launching.
Don't run more than 2-3 epochs on this dataset — overfitting is likely.

---

## How to read the live metrics

`train_dave.py` logs metrics every 10 steps. A typical line looks like:

```
{'loss': '0.943', 'grad_norm': '0.27', 'learning_rate': '0.0001894',
 'entropy': '0.94', 'num_tokens': '7.83e+05',
 'mean_token_accuracy': '0.7931', 'epoch': '0.18'}
```

What each field means:

| Field | What it is | Healthy range |
|---|---|---|
| `loss` | Cross-entropy on next-token prediction (training set). Lower = better. | Starts 2-3, drops to 0.5-1.5 by end |
| `grad_norm` | Magnitude of the optimizer's update. Tells you whether gradients are well-behaved. | 0.1-5 healthy; >50 means trouble |
| `learning_rate` | Current LR per the cosine schedule. Drops over time. | Starts at 2e-4, decays toward 0 |
| `entropy` | Uncertainty across token predictions. Drops as the model gets more confident. | 2 → 0.5 typical |
| `mean_token_accuracy` | Fraction of tokens predicted correctly on this batch. | Climbs from ~30% to 75-90% |
| `epoch` | Fractional epoch progress (0.0 → 1.0 for 1 epoch). | — |
| `num_tokens` | Cumulative tokens processed so far. | — |

### What to actually watch for

**Loss curve shape:**

- **Smooth descent → plateau:** normal, expected. Watch the plateau height —
  if loss bottoms at 0.5-1.0, training is doing real work. If it bottoms
  at 1.5+, the model isn't learning much (consider higher LR or more data).
- **Spikes:** occasional spikes are fine if they recover within ~10 steps.
  Spikes that don't recover usually mean a bad LR — restart with `learning_rate`
  set ~half of the current value.
- **Loss going to 0:** alarming. Means the model is memorizing exact tokens.
  Almost always overfitting, especially with a small dataset.

**Grad norm:**

- 0.1-5: healthy, optimizer is working
- 5-20: aggressive but workable
- 20+: unstable; lower the learning rate
- 50+: gradient explosion; stop and lower LR significantly

**Eval loss** (printed every 100 steps as `eval_loss`):

This is the **single most important number** for deciding when to stop.

- If `eval_loss` is dropping in lockstep with training loss → model is
  generalizing well, keep going.
- If `eval_loss` flattens while training loss keeps dropping → diminishing
  returns; stop soon.
- If `eval_loss` starts climbing while training loss keeps dropping →
  **overfitting**; stop now and use an earlier checkpoint.

---

## Checkpoints — the "best Dave" might not be the *last* Dave

`train_dave.py` writes a checkpoint every 100 steps to
`$DAVE_OUTPUT_DIR/checkpoint-100`, `checkpoint-200`, `checkpoint-300`, etc.,
keeping the most recent 2 plus the final save. **The checkpoint with the
lowest eval_loss is usually the right one to deploy** — not necessarily the
final one.

### Picking the right checkpoint

After training exits, look at the eval lines:

```
{'eval_loss': 1.20, 'eval_runtime': ..., 'step': 100}
{'eval_loss': 0.92, 'eval_runtime': ..., 'step': 200}
{'eval_loss': 0.95, 'eval_runtime': ..., 'step': 300}   <- climbing! overfit starting
```

In that example, `checkpoint-200` is the best Dave. Use it instead of the
final save.

### Loading a non-final checkpoint

The adapter directory layout looks like:

```
dave_adapter/
├── adapter_config.json          # final
├── adapter_model.safetensors    # final
├── checkpoint-100/
├── checkpoint-200/              # use this one
└── checkpoint-300/
```

To use `checkpoint-200`, point your inference code at
`dave_adapter/checkpoint-200/` (it has its own `adapter_config.json` +
`adapter_model.safetensors`).

---

## Three failure modes and what to do about them

### 1. Underfitting (loss never drops below ~2)

Symptoms: loss plateaus high; token accuracy stuck below 50%; outputs
generic/garbled.

Likely causes:
- Learning rate too low — try `learning_rate=4e-4` instead of `2e-4`
- Not enough data variety — add more sources to `build_training_data.sh`
- LoRA rank too low — try `r=32` instead of `r=16` in `train_dave.py`

### 2. Overfitting (eval_loss climbs while train loss falls)

Symptoms: train loss drops to <0.3; eval loss climbs after some step; outputs
parrot training examples verbatim or sound stilted.

Likely causes / fixes:
- Too many epochs — drop `DAVE_EPOCHS` from 2 to 1
- Roll back to the checkpoint with lowest eval_loss
- Dataset too small — increase data, or reduce LoRA rank to slow learning
- Increase dropout — bump `lora_dropout` from 0.05 to 0.1

### 3. Instability (loss spikes, grad_norm explodes)

Symptoms: loss bounces wildly; grad_norm hits 20+; sometimes NaN.

Likely causes / fixes:
- Learning rate too high — halve `learning_rate`
- Sequence length too long — reduce `max_length`
- Mixed-precision overflow — switch from bf16 to fp16 or vice versa
- Bad data — check for corrupted/empty rows in `shuffled_training.jsonl`

---

## When to start over (vs. let it cook)

Restart and reconfigure if:

- Loss plateaus far above 1.5 within the first 25% of training (underfit)
- Grad norm averages above 20 for 20+ consecutive steps (unstable)
- Eval loss climbs by 0.2+ from its minimum (overfit, can't recover)
- You realize the data has a quality issue (always restart after fixing the
  data — partial training on bad data wastes the rest)

Let it ride if:

- Loss is descending smoothly toward 0.5-1.5
- Eval loss is tracking training loss within ~0.3
- Grad norm is under 5 and stable
- Token accuracy is climbing toward 75%+

---

## After training finishes

1. **Check the final state:**
   ```bash
   ls -la "$DAVE_OUTPUT_DIR"
   # expect: adapter_config.json, adapter_model.safetensors, checkpoint-*/
   ```

2. **Pull the eval history** from the log:
   ```bash
   grep eval_loss /workspace/train.log | head -20
   ```

3. **Pick the best checkpoint** (lowest eval_loss).

4. **Retrieve the adapter to your local machine:**
   ```bash
   # On your laptop, from the Dave repo:
   runpodctl receive <send-code-from-pod>
   # Or scp:
   scp -i ~/.runpod/ssh/RunPod-Key-Go -P <port> -r \
       root@<pod-ip>:/workspace/dave_adapter ./dave_adapter
   ```

5. **Test the adapter** with a held-out prompt before declaring victory.
   See `examples/` for inference snippets (TODO — not shipped yet).

6. **Publish the adapter** to Hugging Face Hub (primary) and GitHub Release
   (mirror archive):

   ```bash
   export HF_TOKEN=<write-permission token from huggingface.co/settings/tokens>
   ./scripts/publish_adapter.sh
   ```

   The script:
   - Creates the HF Hub repo (`CryptoJones/Dave-Llama-3.3-70B-QLoRA` by default)
     and uploads the adapter weights + `MODEL_CARD.md` as the model README.
   - Creates a GitHub Release on `CryptoJones/dave` with a tarball of the
     adapter as an attachment, pointing at the HF Hub copy as the canonical
     source.
   - Use `--hf-only` or `--github-only` if you want just one side.
   - Set `DAVE_ADAPTER_DIR=./dave_adapter/checkpoint-N` to publish a specific
     checkpoint instead of the final save (recommended if eval loss showed
     overfitting late in training).

   The read-only HF token used for training **will not work** here — you need
   a token with write access for the upload.

7. **Tear down the pod** as soon as you've confirmed weights landed safely
   (on HF Hub or wherever you've persisted them):

   ```bash
   runpodctl pod remove <pod-id>
   ```

   Pods bill by the hour whether they're training or idle. The first thing
   you do after a successful adapter publish is destroy the pod.

---

## Quick reference: hyperparameters

These are set in `train_dave.py`. Defaults shown.

| Hyperparameter | Default | Notes |
|---|---|---|
| `num_train_epochs` | 1 (`DAVE_EPOCHS`) | 2 is reasonable for a second pass once you've seen the eval curve |
| `learning_rate` | 2e-4 | Standard QLoRA LR. Halve if unstable; double if underfit |
| `lr_scheduler_type` | cosine | Smooth decay; works well at 1-3 epochs |
| `warmup_ratio` | 0.03 | First 3% of steps warm up from 0 to LR |
| `gradient_accumulation_steps` | 16 | Effective batch = batch_size × accum (= 16) |
| `per_device_train_batch_size` | 1 | Increase if you have headroom in VRAM (rare for 70B) |
| `max_length` | 1024 | Covers ~99% of our pairs; raise if you have longer data |
| `packing` | True | Concatenates short pairs to fill sequence length. Huge speedup. |
| LoRA `r` | 16 | Adapter rank. 32 for more capacity, 8 for faster/smaller |
| LoRA `alpha` | 32 | Scaling factor; convention is r × 2 |
| LoRA `dropout` | 0.05 | Bump to 0.1 if overfitting |
| `optim` | paged_adamw_8bit | 8-bit AdamW; paged means CPU-offload on memory pressure |
