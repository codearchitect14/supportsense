from pydantic import BaseModel, ConfigDict


class StrictRequestModel(BaseModel):
    """Base for request bodies: rejects any field the client didn't declare,
    rather than silently ignoring it.
    """

    model_config = ConfigDict(extra="forbid")
