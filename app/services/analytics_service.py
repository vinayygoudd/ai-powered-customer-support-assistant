class AnalyticsService:
    def __init__(self, db):
        self.db = db

    def summary(self):
        return self.db.analytics()
