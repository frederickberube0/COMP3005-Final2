#### Conceptual Design ####

The database will contain many tables.
These will mainly include tables directly related to the user like User, Admins, Trainers, Members.
Admin, Trainers, Members will all represent one-to-one relationship with the User table, where each of admin, trainer, member can log into using User. 

Obviously we could have put the User columns in each of the other three tables, for example the member table could have Passwords, however we
wanted every user created to have a unique ID in the entire database. For example, there won't be a Member and an Admin with the same ID. This
gives us more flexibility. for example, in the future if we want to promote a Member to a trainer, we can re-use that same id.

# Cardinality 

- One-to-one: Each Member-User, Admin-User, Trainer-User is a one-to-one relationship.
- Many-to-many: One event can have many different attendees, and one attendee can attend many different events

# Assumptions

Some assumptions made:
- Admin will have to create rooms and set that room's availability before somoene can book it.
- Admins assign trainers to lead group fitness classes.
- Trainers can decide their own availability.
- Equipment can only be maintained at specific intervals (daily, weekly, etc...) Not every 7th week.
- The database will likely have to be reset weekly or something similar to ensure passed classes are removed from the database once the scheduled time has passed.
- The gym is free unless you book a class.
