import octoprint.plugin
import requests
from octoprint.events import Events


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


class MaintenanceReminderPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.EventHandlerPlugin,
):
    def get_settings_defaults(self):
        return {
            "reminders": [
                {"message": "Clean and lubricate smooth rods", "interval": 200, "hours": 0},
                {"message": "Clean fans", "interval": 200, "hours": 0},
            ],
            "notify_pushover": True,
            "show_navbar_message": True,
            "warning_threshold": 50,
            "danger_threshold": 80,
        }

    def get_assets(self):
        return {
            "js": ["js/maintenance_reminder.js"],
            "css": ["css/maintenance_reminder.css"],
            "less": ["less/maintenance_reminder.less"],
        }

    def get_update_information(self):
        return {
            "maintenance_reminder": {
                "displayName": "Maintenance Reminder",
                "displayVersion": self._plugin_version,
                "type": "github_release",
                "user": "Chaldron",
                "repo": "OctoPrint-Maintenance-Reminder",
                "current": self._plugin_version,
                "pip": "https://github.com/Chaldron/OctoPrint-Maintenance-Reminder/archive/{target_version}.zip",
            }
        }

    def on_event(self, event, payload):
        # A cancelled print fires PrintCancelled and then PrintFailed, so only PrintFailed is counted.
        if event not in (Events.PRINT_DONE, Events.PRINT_FAILED):
            return

        printed_hours = number(payload.get("time")) / 3600
        if printed_hours <= 0:
            return

        reminders = self._settings.get(["reminders"])
        newly_due_reminders = []
        for reminder in reminders:
            interval = number(reminder.get("interval"))
            hours_before = number(reminder.get("hours"))
            reminder["hours"] = round(hours_before + printed_hours, 3)
            if interval > 0 and hours_before < interval <= reminder["hours"]:
                newly_due_reminders.append(reminder)

        self._settings.set(["reminders"], reminders)
        self._settings.save()
        self._logger.info("Added %.2f print hours to %d reminders", printed_hours, len(reminders))

        self._plugin_manager.send_plugin_message(
            self._identifier, {"type": "reminders_updated", "reminders": reminders}
        )

        if newly_due_reminders and self._settings.get_boolean(["notify_pushover"]):
            self.notify_pushover(newly_due_reminders)

    def notify_pushover(self, due_reminders):
        token = self._settings.global_get(["plugins", "pushover", "token"])
        user_key = self._settings.global_get(["plugins", "pushover", "user_key"])
        if not token or not user_key:
            self._logger.info("Pushover plugin has no token and user key, not notifying")
            return

        message = "\n".join(
            "{} ({:g} h)".format(reminder["message"], number(reminder["interval"]))
            for reminder in due_reminders
        )

        try:
            response = requests.post(
                "https://api.pushover.net/1/messages.json",
                data={
                    "token": token,
                    "user": user_key,
                    "title": "Printer maintenance due",
                    "message": message,
                },
                timeout=10,
            )
            self._logger.info("Pushover notification sent, status %s", response.status_code)
        except requests.RequestException as error:
            self._logger.warning("Pushover notification failed: %s", error)

    def get_template_configs(self):
        return [
            dict(type="settings", custom_bindings=True),
            dict(type="navbar", custom_bindings=True, classes=["dropdown"]),
            dict(type="generic", template="maintenance_reminder_modal.jinja2"),
        ]

    def is_template_autoescaped(self):
        return True


__plugin_name__ = "Maintenance Reminder"
__author__ = "Garron Anderson <garronanderson4321@gmail.com>"
__plugin_pythoncompat__ = ">=3.7,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = MaintenanceReminderPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
