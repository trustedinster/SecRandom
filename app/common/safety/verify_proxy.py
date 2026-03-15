def require_and_run_lazy(*args, **kwargs):
    """Lazily import the verification entrypoint on demand."""
    from app.common.safety.verify_ops import require_and_run

    return require_and_run(*args, **kwargs)
