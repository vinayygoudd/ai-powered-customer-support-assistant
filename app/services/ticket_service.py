HIGH_RISK_KEYWORDS = {
    "fraud", "fraudulent", "hacked", "stolen", "unauthorized",
    "lawsuit", "legal", "security breach", "identity theft",
}


class TicketService:
    """Coordinates ticket persistence, ML prediction, review routing and AI response."""

    def __init__(self, db, ml, llm, prompts, queue):
        self.db = db
        self.ml = ml
        self.llm = llm
        self.prompts = prompts
        self.queue = queue

    def create_ticket(self, user_id, message):
        return self.db.create_ticket(user_id, message)

    def predict_ticket(self, ticket_id, message=None, conn=None):
        # IMPORTANT: use the caller's transaction connection when supplied.
        # The ticket may not be committed yet, so a separate connection cannot
        # see it.
        ticket = self.db.get_ticket(ticket_id, conn=conn)
        if not ticket:
            raise ValueError("Ticket not found")

        text = message or ticket["message"]
        prediction = self.ml.predict(text)
        lower = text.lower()
        human_review = (
            prediction["priority"] == "Critical"
            or any(keyword in lower for keyword in HIGH_RISK_KEYWORDS)
        )

        self.db.update_ticket_prediction(
            ticket_id,
            prediction["category"],
            prediction["priority"],
            human_review,
            conn=conn,
        )
        self.db.add_prediction(
            ticket_id,
            prediction["category"],
            prediction["priority"],
            prediction["model_version"],
            conn=conn,
        )

        return {
            **prediction,
            "human_review_required": human_review,
        }

    def generate_response(self, ticket_id, conn=None):
        # Use the same transaction connection so this read sees the prediction
        # written immediately before it, even before COMMIT.
        ticket = self.db.get_ticket(ticket_id, conn=conn)
        if not ticket:
            raise ValueError("Ticket not found")

        context = {
            "customer_message": ticket["message"],
            "predicted_category": ticket["category"] or "Unknown",
            "predicted_priority": ticket["priority"] or "Unknown",
            "ticket_status": ticket["status"],
            "human_review_required": bool(ticket["human_review_required"]),
        }

        if context["human_review_required"]:
            prompt = (
                self.prompts.escalation_prompt(**context)
                + "\n\n"
                + self.prompts.response_prompt(**context)
            )
        else:
            prompt = self.prompts.response_prompt(**context)

        try:
            response = self.llm.generate(prompt)
        except Exception:
            response = self.llm.safe_fallback()

        if not self.llm.validate_response(response):
            response = self.llm.safe_fallback()

        self.db.add_ai_interaction(
            ticket_id,
            self.prompts.VERSION,
            response,
            conn=conn,
        )

        return {
            "response": response,
            "prompt_version": self.prompts.VERSION,
        }

    def process_ticket_atomic(self, user_id, message):
        """Process a ticket with one database transaction.

        Ticket creation, prediction persistence and AI-interaction persistence
        all commit together. The in-memory priority queue is updated only after
        the database transaction commits, preventing a queue entry for a rolled
        back ticket.
        """
        with self.db.transaction() as conn:
            ticket_id = self.db.create_ticket(
                user_id,
                message,
                conn=conn,
            )
            prediction = self.predict_ticket(
                ticket_id,
                message=message,
                conn=conn,
            )
            ai = self.generate_response(
                ticket_id,
                conn=conn,
            )

            result = {
                "ticket_id": ticket_id,
                "prediction": prediction,
                "ai_response": ai["response"],
                "prompt_version": ai["prompt_version"],
            }

        # Only enqueue after the transaction has successfully committed.
        self.queue.add(ticket_id, prediction["priority"])
        return result
