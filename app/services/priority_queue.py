import heapq
from dataclasses import dataclass, field

PRIORITY_RANK = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

@dataclass(order=True)
class QueueItem:
    rank: int
    sequence: int
    ticket_id: int = field(compare=False)

class PriorityQueueManager:
    def __init__(self):
        self._heap = []
        self._sequence = 0
        self._seen = set()

    def add(self, ticket_id, priority):
        if ticket_id in self._seen:
            return
        heapq.heappush(self._heap, QueueItem(PRIORITY_RANK.get(priority, 3), self._sequence, ticket_id))
        self._sequence += 1
        self._seen.add(ticket_id)

    def pop_next(self):
        if not self._heap:
            return None
        item = heapq.heappop(self._heap)
        self._seen.discard(item.ticket_id)
        return item.ticket_id

    def __len__(self):
        return len(self._heap)
