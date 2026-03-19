
#!/usr/bin/python3

## ---------------------------------------------------------------------
##
##  A hack to preprocess Modsecurity JSON logs into a proper JSON format
##  Hopefully this can be removed as soon as ModSecurity updates to not to
##  have a shitty format for the actual audit_data
##
## ----------------------------------------------------------------------

import json
import re
import time
import logging
from typing import Tuple, List, Dict, Any, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


class LineParser:
    """Parses audit_log.messages and audit_log.error_messages"""
    __tagRegex__ = r' {{{{\[.*? .*?\]}}}}|^{{{{\[.*? .*?\]}}}}'

    def __parseTag__(self, tag) -> Tuple[str, str]:
        tag = tag.strip()
        tag = tag[1:-1]
        tag = tag.split(" ", 1)
        key = tag[0]
        value = tag[1][1:-1] if tag[1].startswith("\"") else tag[1]
        return (key, value)

    def __parseMessages__(self, messages) -> Dict[str, Any]:
        events: Dict[str, Any] = {}
        index = 0

        for message in messages or []:
            event: Dict[str, Any] = {}

            tags = re.findall(self.__tagRegex__, message)
            for chunk in tags:
                key, value = self.__parseTag__(chunk)
                if key == "tag":
                    event.setdefault("tags", []).append(value)
                else:
                    event[key] = value

            leftovers = re.sub(self.__tagRegex__, "", message)
            leftovers = leftovers.split(".", 1)
            event["type"] = leftovers[0].strip()
            event["pattern"] = leftovers[1].strip() if len(leftovers) > 1 else ""

            # Logstash can't process nested object arrays so we use dict keys
            events[f"message-{index}"] = event
            index += 1

        return events

    def parse(self, logLine) -> Dict[str, Any]:
        parsed = json.loads(logLine)

        parsed["messages"] = self.__parseMessages__(parsed.get("audit_data", {}).get("messages", []))
        parsed["error_messages"] = self.__parseMessages__(parsed.get("audit_data", {}).get("error_messages", []))

        if "audit_data" in parsed:
            parsed["audit_data"].pop("messages", None)
            parsed["audit_data"].pop("error_messages", None)

        return parsed


class FileHandler(FileSystemEventHandler):
    parser = LineParser()
    originalPath = "/var/log/modsec_audit.log"
    processedPath = "/var/log/modsec_audit_processed.log"

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith("modsec_audit.log"):
            log.info("Logfile changed")
            self.processLog()

    def processLog(self) -> None:
        processedLines = self.getLines(self.processedPath)
        lines = self.getLines(self.originalPath)

        if not lines:
            return

        procIndex = 0 if processedLines is None else len(processedLines)
        log.debug("Processed file lines %s", procIndex)

        origIndex = len(lines)
        log.debug("Original file lines %s", origIndex)

        index, writeMode = self.getHead(origIndex, procIndex)
        log.debug("Head %s", index)
        log.debug("Write Mode %s", writeMode)

        newLines = []
        for i in range(index, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            try:
                newLines.append(json.dumps(self.parser.parse(line)))
            except Exception:
                log.exception("Failed to parse line %s", i)

        try:
            with open(self.processedPath, writeMode, encoding="utf-8") as f:
                for line in newLines:
                    f.write(line + "\n")
        except Exception:
            log.exception("Error writing to processed log")

    def getLines(self, path) -> Optional[List[str]]:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.readlines()
        except FileNotFoundError:
            return None

    def getHead(self, origFileIndex: int, newFileIndex: int) -> Tuple[int, str]:
        # returns (index, write mode)
        # If original log rotated/truncated (orig <= processed), rewrite from start.
        if origFileIndex <= newFileIndex:
            return (0, "w")
        if newFileIndex == 0:
            return (0, "a")
        if newFileIndex > 0 and origFileIndex > newFileIndex:
            return (newFileIndex, "a")
        raise NotImplementedError("Case not implemented")


if __name__ == "__main__":
    PATH = "/var/log/"

    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s][%(levelname)s][%(name)s] %(message)s'
    )
    log = logging.getLogger("Python-Script")

    handler = logging.FileHandler("/var/log/preprocess-script.log")
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s][%(name)s] %(message)s')
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    log.addHandler(handler)

    log.info("Python script is starting up...")

    event_handler = FileHandler()
    observer = Observer()
    observer.schedule(event_handler, PATH, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
