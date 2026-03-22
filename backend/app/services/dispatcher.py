from app.models.inference_job import InferenceJob


class InferenceDispatcher:
    def dispatch(self, job: InferenceJob) -> None:
        # Milestone 2A queues jobs only. Real engine dispatch starts in Milestone 2B.
        _ = job