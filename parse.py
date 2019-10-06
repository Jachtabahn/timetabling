from xml import sax
import logging
import argparse

class Time:

   def __init__(self, weeks, days, start, length):
      self.weeks = weeks
      self.days = days
      self.start = start
      self.length = length

   def __str__(self):
      return f'In the weeks {self.weeks}, the days {self.days}, in the time slots {self.start}-{self.start+self.length-1}.'

# this maps a frozenset of rooms to a number, the distance between these rooms in time slots
room_distances = dict()

# maps an id to a Room object
room_by_id = dict()
class Room:

   def __init__(self, room_id):
      self.id = room_id
      self.unavailable_times = []

   def add_unavailable(self, time_location):
      self.unavailable_times.append(time_location)

   def __str__(self):
      if not self.unavailable_times:
         return f'Room {self.id} is always available.\n'
      s = f'Room {self.id} is unavailable:\n'
      for time_location in self.unavailable_times:
         s += f'{time_location}\n'
      return s

'''
   A uclass represents a university class.
'''
uclass_by_id = dict()
class Uclass:

   def __init__(self, uclass_id):
      self.id = uclass_id
      self.times = dict()
      self.rooms = dict()

      '''
         The following dictionary maps a string like 'NotOverlap' or 'SameAttendees' to a dictionary.
         This dictionary maps a uclass to a penalty. This penalty is an integer or float('inf'). Infinity is used to
         indicate that a constraint must be met in a feasible solution.
      '''
      self.distributions = dict()

   def add_time(self, time_location, penalty):
      self.times[time_location] = penalty

   def add_room(self, room, penalty):
      self.rooms[room] = penalty

   def add_constraint(self, distribution_type, distribution_penalty, other_uclass):
      if distribution_type not in self.distributions:
         self.distributions[distribution_type] = dict()
      if other_uclass not in self.distributions[distribution_type]:
         self.distributions[distribution_type][other_uclass] = 0
      self.distributions[distribution_type][other_uclass] += distribution_penalty

   def __str__(self):
      s = f'Class {self.id} has {len(self.times)} possible times, {len(self.rooms)} possible rooms'
      s += f' and {len(self.distributions)} different constraint types:\n'
      for room, penalty in self.rooms.items():
         s += f'Room {room.id} has penalty {penalty}.\n'
      for time_location, penalty in self.times.items():
         s += f'{time_location} This time has penalty {penalty}.\n'
      for distribution_name, specific_constraints in self.distributions.items():
         s += f'Distribution of type "{distribution_name}":\n'
         for uclass, penalty in specific_constraints.items():
            s += f'Violation of this distribution with class {uclass.id} leads to a penalty of {penalty}.\n'
      return s

class TimetablingHandler(sax.ContentHandler):

   def __init__(self):
      '''
         Indicates an important node up the branch, where we are in the XML tree at the moment. This context allows us
         to distinguish, for example, the two occurrences of the 'room' element when it's described itself,
         versus when it's used to describe a class.

         Takes values in ['rooms, 'subpart', None].
      '''
      self.section = None
      self.current_room = None
      self.current_uclass = None

      self.distribution_type = None
      self.distribution_penalty = None
      self.distribution_uclasses = None

   def startElement(self, tag, attributes):
      # parse the rooms
      if tag == 'rooms':
         self.section = tag
      elif tag == 'room' and self.section == 'rooms':
         room_id = int(attributes['id'])
         self.current_room = Room(room_id)
         room_by_id[room_id] = self.current_room
      elif tag == 'unavailable' and self.current_room is not None:
         weeks = attributes['weeks']
         days = attributes['days']
         start = int(attributes['start'])
         length = int(attributes['length'])
         time_location = Time(weeks, days, start, length)
         self.current_room.add_unavailable(time_location)
      elif tag == 'travel' and self.current_room is not None:
         other_room_id = int(attributes['room'])
         both_room_ids = frozenset([self.current_room.id, other_room_id])
         distance = int(attributes['value'])
         room_distances[both_room_ids] = distance

      # parse the classes
      elif tag == 'subpart':
         self.section = tag
      elif tag == 'class' and self.section == 'subpart':
         uclass_id = int(attributes['id'])
         self.current_uclass = Uclass(uclass_id)
         uclass_by_id[uclass_id] = self.current_uclass
      elif tag == 'room' and self.current_uclass is not None:
         penalty = int(attributes['penalty'])
         room_id = int(attributes['id'])
         room = room_by_id[room_id]
         self.current_uclass.add_room(room, penalty)
      elif tag == 'time' and self.current_uclass is not None:
         penalty = int(attributes['penalty'])
         weeks = attributes['weeks']
         days = attributes['days']
         start = int(attributes['start'])
         length = int(attributes['length'])
         time_location = Time(weeks, days, start, length)
         self.current_uclass.add_time(time_location, penalty)

      # parse the distributions
      elif tag == 'distributions':
         self.section = tag
      elif tag == 'distribution':
         self.distribution_type = attributes['type']
         self.distribution_penalty = int(attributes['penalty']) if 'penalty' in attributes else float('inf')
         self.distribution_uclasses = []
      elif tag == 'class' and self.distribution_uclasses is not None:
         uclass_id = int(attributes['id'])
         uclass = uclass_by_id[uclass_id]
         self.distribution_uclasses.append(uclass)

   def endElement(self, tag):
      if tag == 'rooms':
         self.section = None
      elif tag == 'room':
         self.current_room = None
      elif tag == 'subpart':
         self.section = None
      elif tag == 'class' and self.current_uclass is not None:
         self.current_uclass = None
      elif tag == 'distributions':
         self.section = None
      elif tag == 'distribution':
         for uclass in self.distribution_uclasses:
            for other_uclass in self.distribution_uclasses:
               if other_uclass == uclass: continue
               uclass.add_constraint(self.distribution_type, self.distribution_penalty, other_uclass)
         self.distribution_type = None
         self.distribution_penalty = None
         self.distribution_uclasses = None

if __name__ == '__main__':
   parser = argparse.ArgumentParser()
   parser.add_argument('--verbose', '-v', action='count')
   args = parser.parse_args()
   log_levels = {
       None: logging.WARNING,
       1: logging.INFO,
       2: logging.DEBUG
   }
   logging.basicConfig(format='%(message)s', level=log_levels[args.verbose])

   parser = sax.make_parser()
   parser.setContentHandler(TimetablingHandler())
   parser.parse('instances/agh-fis-spr17.xml')

   print(f'I found the rooms:\n')
   for room_id, room in room_by_id.items():
      print(f'{room}')

   print(f'The room distances are:\n')
   for two_rooms, distance in room_distances.items():
      print(f'Rooms {two_rooms} have distance {distance}\n')

   print('The classes are:')
   for uclass_id, uclass in uclass_by_id.items():
      print(uclass)
