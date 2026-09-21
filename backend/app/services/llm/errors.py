class LLMProviderError(Exception):
    """A provider call failed for a reason other than rate limiting."""


class LLMRateLimitError(LLMProviderError):
    """A provider signaled that its rate limit or quota has been exhausted."""


class AllProvidersExhaustedError(Exception):
    """Every configured provider is rate limited, over quota, or failing."""
