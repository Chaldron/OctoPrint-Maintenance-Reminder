# OctoPrint-Maintenance-Reminder

Fork of [GarronAnderson/OctoPrint-Maintenance-Reminder](https://github.com/GarronAnderson/OctoPrint-Maintenance-Reminder) that tracks print hours instead of print counts.

Every finished, failed or cancelled print adds its print time to each reminder. A reminder is due once its hours reach its interval: the navbar turns red, a dialog appears before the next print, and a Pushover message is sent through the token and user key of the Pushover plugin. "Mark Complete" resets a reminder to zero.

Only prints run through OctoPrint are counted. To seed a reminder, type the hours already printed into its hours field under Settings > Maintenance Reminder.

## Setup

    pip install https://github.com/Chaldron/OctoPrint-Maintenance-Reminder/archive/master.zip
