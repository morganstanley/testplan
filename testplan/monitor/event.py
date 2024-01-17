import time
import dataclasses
from typing import Dict, List, Optional, Union

#
# @dataclasses.dataclass
# class EventRecorder:
#     name: str
#     event_type: str
#     start_time: Optional[float] = None
#     end_time: Optional[float] = None
#     children: List["EventRecorder"] = dataclasses.field(default_factory=list)
#
#     @classmethod
#     def load(
#         cls, event_record: Union["EventRecorder", Dict]
#     ) -> "EventRecorder":
#         if isinstance(event_record, cls):
#             return event_record
#
#         event = cls(
#             name=event_record["name"],
#             event_type=event_record["event_type"],
#             start_time=event_record["start_time"],
#             end_time=event_record["start_time"],
#         )
#         if event_record.get("children"):
#             for child in event_record["children"]:
#                 event.children.append(cls.load(child))
#         return event
#
#     def __enter__(self):
#         self.start_time = time.time()
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.end_time = time.time()
#
#     def add_child(self, event_executor: "EventRecorder"):
#         self.children.append(event_executor)
