import asyncio
from datetime import datetime

import pytest

from modules.slack_report import send_email_report, send_slack_report


@pytest.hookimpl(tryfirst=True)
def pytest_terminal_summary(terminalreporter, *_):
    report_data = []
    for (key,rep) in terminalreporter.stats.items():
        if key in {"warnings",""}:
            continue
        for sub_rep in rep:
            if issue_msg := sub_rep._to_json().get("longrepr"):
                issue_msg = issue_msg["reprcrash"]["message"].replace("\n","")
            name = sub_rep.head_line.split(".")[-1]
            location = f"{sub_rep.nodeid}:{sub_rep.location[1]}"
            success = sub_rep.passed
            failure_reason = sub_rep.longreprtext if not success else ""
            report_tuple = (name,datetime.now(),":passed:" if success else ":failed:", location, failure_reason, issue_msg)
            report_data.append(report_tuple)
    msg = asyncio.run(send_slack_report(report_data))
    asyncio.run(send_email_report(*msg))
    
