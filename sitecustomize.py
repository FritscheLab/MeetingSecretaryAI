"""Python startup customizations for MeetingSecretaryAI.

This file is automatically imported by Python (via the built-in `site` module)
when it is present on `sys.path`.

We use it to improve compatibility with recent PyTorch versions where
`torch.load(..., weights_only=True)` is the default. Some third-party model
checkpoints (notably pyannote/Lightning) include OmegaConf container types in
metadata, which require being added to PyTorch's safe unpickling allowlist.

This does NOT disable `weights_only` and does not opt into arbitrary code
execution; it only adds specific, commonly used OmegaConf container classes to
the safe globals.
"""

from __future__ import annotations


def _configure_torch_safe_globals() -> None:
    try:
        import torch
    except Exception:
        return

    add_safe_globals = getattr(getattr(torch, "serialization", None), "add_safe_globals", None)
    if add_safe_globals is None:
        return

    try:
        from omegaconf.dictconfig import DictConfig
        from omegaconf.listconfig import ListConfig
    except Exception:
        return

    try:
        add_safe_globals([DictConfig, ListConfig])
    except Exception:
        # Best-effort only; if this fails we fall back to default behavior.
        return


_configure_torch_safe_globals()
