#!/usr/bin/env python3

import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import tempfile
import uuid


class AlfredWorkflow:
    def __init__(self):
        self.metadata = {
            "bundleid": "alexwlchan.aws-console-roles",
            "category": "Internet",
            "connections": {},
            "createdby": "@alexwlchan",
            "description": "Shortcuts to open roles in the AWS console",
            "name": "AWS console roles",
            "objects": [],
            "readme": "",
            "uidata": {},
            "version": "1.0.0",
            "webaddress": "https://github.com/alexwlchan/github_alfred_shortcuts",
        }
        self.icons = {}

    def add_script(self, language, title, shortcut, filename, icon=None):
        script_types = {
            "shell": 0,
            "python": 9,
        }

        trigger_object = {
            "config": {
                "argumenttype": 0 if "{query}" in title else 2,
                "keyword": shortcut,
                "subtext": "",
                "text": title,
                "withspace": True,
            },
            "type": "alfred.workflow.input.keyword",
            "uid": self.uuid("shortcut", shortcut, title),
            "version": 1,
        }

        with open(filename) as infile:
            script_body = infile.read()

        script_object = {
            "config": {
                "concurrently": False,
                "escaping": 102,
                "script": script_body,
                "scriptargtype": 1,
                "scriptfile": "",
                "type": script_types[language],
            },
            "type": "alfred.workflow.action.script",
            "uid": self.uuid("script", script_body),
            "version": 2,
        }

        self._add_trigger_action_pair(
            trigger_object=trigger_object, action_object=script_object, icon=icon
        )

    def add_aws_console_shortcuts(self, name, color, account_id):
        if not os.path.exists(f"icons/iam_role_{color}.png"):
            svg = open("iam_role.svg").read()

            os.makedirs("icons", exist_ok=True)

            with open(f"icons/iam_role_{color}.svg", "w") as outfile:
                outfile.write(svg.replace('fill="#BF0816"', f'fill="#{color}"'))

            subprocess.check_call(
                [
                    "convert",
                    "-background",
                    "none",
                    "-density",
                    "500",
                    f"icons/iam_role_{color}.svg",
                    f"icons/iam_role_{color}.png",
                ]
            )

        icon = f"icons/iam_role_{color}.png"

        script_base = open("open_role_in_console.py.template").read()

        script_code = (
            script_base.replace("{ROLE_NAME}", repr(f"{name}"))
            .replace("{COLOR}", repr(color))
            .replace("{ACCOUNT_ID}", repr(account_id))
            .replace("{DISPLAY_NAME}", repr(name))
        )

        _, script_tmp_file = tempfile.mkstemp()
        open(script_tmp_file, "w").write(script_code)

        self.add_script(
            language="python",
            title=f"Open AWS role {name}",
            shortcut=name,
            filename=os.path.abspath(script_tmp_file),
            icon=icon,
        )

        os.unlink(script_tmp_file)

    def uuid(self, *args):
        assert len(args) > 0
        md5 = hashlib.md5()
        for a in args:
            md5.update(a.encode("utf8"))

        # Quick check we don't have colliding UUIDs.
        if not hasattr(self, "_md5s"):
            self._md5s = {}
        hex_digest = md5.hexdigest()
        assert hex_digest not in self._md5s, (args, self._md5s[hex_digest])
        self._md5s[hex_digest] = args

        return str(uuid.UUID(hex=hex_digest)).upper()

    def _add_trigger_action_pair(self, trigger_object, action_object, icon):
        self.metadata["objects"].append(trigger_object)
        self.metadata["objects"].append(action_object)

        self.icons[trigger_object["uid"]] = icon

        if not hasattr(self, "idx"):
            self.idx = 0

        self.metadata["uidata"][trigger_object["uid"]] = {
            "xpos": 150,
            "ypos": 50 + 120 * self.idx,
        }
        self.metadata["uidata"][action_object["uid"]] = {
            "xpos": 600,
            "ypos": 50 + 120 * self.idx,
        }
        self.idx += 1

        self.metadata["connections"][trigger_object["uid"]] = [
            {
                "destinationuid": action_object["uid"],
                "modifiers": 0,
                "modifiersubtext": "",
                "vitoclose": False,
            },
        ]

    def assemble_package(self, name):
        with tempfile.TemporaryDirectory() as tmp_dir:
            shutil.copyfile("iam.png", os.path.join(tmp_dir, "Icon.png"))

            for icon_id, icon_path in self.icons.items():
                shutil.copyfile(icon_path, os.path.join(tmp_dir, f"{icon_id}.png"))

            plist_path = os.path.join(tmp_dir, "Info.plist")
            plistlib.dump(self.metadata, open(plist_path, "wb"))

            shutil.make_archive(
                base_name=f"{name}.alfredworkflow", format="zip", root_dir=tmp_dir
            )
            shutil.move(f"{name}.alfredworkflow.zip", f"{name}.alfredworkflow")


if __name__ == "__main__":
    workflow = AlfredWorkflow()

    color_map = {
        'red': 'F2B0A9',
        'orange': 'FBBF93',
        'yellow': 'FAD791',
        'green': 'B7CA9D',
        'blue': '99BCE3',
    }

    for account in json.load(open("accounts.json")):
        for name in account['role_names']:
            workflow.add_aws_console_shortcuts(account_id=account['id'], name=name, color=color_map[account['color']])

    workflow.assemble_package(name="aws_console_roles")
