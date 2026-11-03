import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "aegis.db"

st.set_page_config(page_title="Aegis AI Governance", page_icon="-_-", layout="wide")

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def log_action(entity_type, entity_id, action, details):
    with db() as conn:
        conn.execute(
            "INSERT INTO audit_log (timestamp, entity_type, entity_id, action, details) VALUES (?, ?, ?, ?, ?)",
            (now(), entity_type, str(entity_id), action, details)
        )

def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS ai_systems (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            purpose TEXT NOT NULL,
            deployment_context TEXT NOT NULL,
            data_types TEXT NOT NULL,
            preliminary_risk TEXT NOT NULL,
            eu_ai_act_classification TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS framework_controls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            framework TEXT NOT NULL,
            reference TEXT NOT NULL,
            requirement_summary TEXT NOT NULL,
            nist_function TEXT NOT NULL,
            mapping_rationale TEXT NOT NULL,
            applicability_note TEXT NOT NULL,
            source_url TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_id INTEGER NOT NULL,
            control_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            evidence TEXT NOT NULL,
            gap TEXT NOT NULL,
            owner TEXT NOT NULL,
            due_date TEXT NOT NULL,
            assessed_at TEXT NOT NULL,
            FOREIGN KEY(system_id) REFERENCES ai_systems(id),
            FOREIGN KEY(control_id) REFERENCES framework_controls(id)
        );
        CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            system_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            incident_type TEXT NOT NULL,
            description TEXT NOT NULL,
            severity TEXT NOT NULL,
            status TEXT NOT NULL,
            impact TEXT NOT NULL,
            containment TEXT NOT NULL,
            root_cause TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(system_id) REFERENCES ai_systems(id)
        );
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            incident_id INTEGER NOT NULL,
            task TEXT NOT NULL,
            owner TEXT NOT NULL,
            status TEXT NOT NULL,
            due_date TEXT NOT NULL,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(incident_id) REFERENCES incidents(id)
        );
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL
        );
        """)

        count = conn.execute("SELECT COUNT(*) FROM framework_controls").fetchone()[0]
        if count == 0:
            controls = [
                ("Risk management system", "EU AI Act", "Article 9",
                 "For applicable high-risk AI systems, establish, implement, document and maintain a risk-management system across the lifecycle.",
                 "MANAGE; MAP; MEASURE",
                 "Risk management and evaluation outcomes can support implementation of Article 9 obligations; this is a working crosswalk, not legal equivalence.",
                 "Confirm system classification, provider role, applicable dates and relevant Article 9 requirements.",
                 "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"),
                ("Data and data governance", "EU AI Act", "Article 10",
                 "For applicable high-risk AI systems, assess relevant data governance and data quality practices for training, validation and testing data.",
                 "MAP; MEASURE",
                 "Data provenance, representativeness, quality and evaluation evidence support risk identification and measurement.",
                 "Confirm applicability to the system and the relevant statutory conditions.",
                 "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"),
                ("Technical documentation", "EU AI Act", "Article 11",
                 "Maintain required technical documentation for applicable high-risk AI systems.",
                 "GOVERN; MAP",
                 "Documentation and ownership support accountability and understanding of system context.",
                 "Requirements vary by role, system category and applicable date.",
                 "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"),
                ("Record-keeping and logs", "EU AI Act", "Article 12",
                 "Applicable high-risk systems are designed to enable automatic recording of events over their lifetime, as required by the Act.",
                 "GOVERN; MEASURE; MANAGE",
                 "Logging supports monitoring, incident investigation and traceability.",
                 "Check specific Article 12 requirements and system/operator responsibilities.",
                 "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"),
                ("Human oversight", "EU AI Act", "Article 14",
                 "Applicable high-risk systems must be designed to enable effective human oversight under the applicable conditions.",
                 "GOVERN; MANAGE",
                 "Named reviewers, override procedures and escalation paths support accountable oversight.",
                 "Confirm system classification and specific oversight requirements.",
                 "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"),
                ("Accuracy, robustness and cybersecurity", "EU AI Act", "Article 15",
                 "Applicable high-risk systems must meet relevant accuracy, robustness and cybersecurity requirements.",
                 "MEASURE; MANAGE",
                 "Evaluation, resilience tests and remediation verification support measurement and risk treatment.",
                 "Use relevant requirements and standards for the system; this summary is not exhaustive.",
                 "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"),
                ("Post-market monitoring", "EU AI Act", "Article 72",
                 "Providers of applicable high-risk AI systems must operate a post-market monitoring system under the applicable requirements.",
                 "MEASURE; MANAGE",
                 "Ongoing monitoring and feedback loops support detection of emerging risks.",
                 "Confirm provider role, classification and application dates.",
                 "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"),
                ("Serious-incident reporting", "EU AI Act", "Article 73",
                 "Assess and report serious incidents where the Article's definitions, conditions and timelines apply.",
                 "MANAGE; GOVERN",
                 "An incident workflow can collect facts and flag a reporting assessment for a responsible person.",
                 "Never infer that every incident is reportable. Legal applicability and timelines require qualified review.",
                 "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"),
                ("Policies and accountability", "NIST AI RMF 1.0", "GOVERN",
                 "Establish policies, roles, accountability, oversight and a risk-management culture.",
                 "GOVERN",
                 "System owners, risk owners, approvals and audit trails operationalize governance activities.",
                 "NIST AI RMF is voluntary guidance unless adopted through another obligation or commitment.",
                 "https://www.nist.gov/itl/ai-risk-management-framework"),
                ("Context and impacts", "NIST AI RMF 1.0", "MAP",
                 "Identify intended purpose, context, stakeholders, benefits, costs and potential impacts.",
                 "MAP",
                 "Context records and stakeholder-impact assessments help scope risk analysis.",
                 "Tailor activities to the use case and organizational context.",
                 "https://www.nist.gov/itl/ai-risk-management-framework"),
                ("Risk analysis and testing", "NIST AI RMF 1.0", "MEASURE",
                 "Use appropriate methods to analyze, assess, benchmark and monitor AI risks and trustworthiness characteristics.",
                 "MEASURE",
                 "Test plans, metrics, evaluation results and limitations provide evidence about risk.",
                 "Metrics must be appropriate to the application and interpreted with context.",
                 "https://www.nist.gov/itl/ai-risk-management-framework"),
                ("Risk treatment and monitoring", "NIST AI RMF 1.0", "MANAGE",
                 "Prioritize and respond to identified risks, select treatment options and monitor outcomes.",
                 "MANAGE",
                 "Incident playbooks, remediation tasks, retesting and risk acceptance support risk treatment.",
                 "Document rationale for accepting residual risk and retain appropriate oversight.",
                 "https://www.nist.gov/itl/ai-risk-management-framework"),
            ]
            conn.executemany("""
                INSERT INTO framework_controls
                (title, framework, reference, requirement_summary, nist_function,
                 mapping_rationale, applicability_note, source_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, controls)

init_db()

def read_df(query, params=()):
    with db() as conn:
        return pd.read_sql_query(query, conn, params=params)

def systems():
    return read_df("SELECT * FROM ai_systems ORDER BY id DESC")

def control_options():
    return read_df("SELECT id, title, framework, reference FROM framework_controls ORDER BY framework, id")

def incident_options():
    return read_df("""SELECT i.*, s.name AS system_name FROM incidents i
                      JOIN ai_systems s ON s.id=i.system_id ORDER BY i.id DESC""")

def set_status(table, record_id, status):
    with db() as conn:
        conn.execute(f"UPDATE {table} SET status=? WHERE id=?", (status, record_id))
    log_action(table, record_id, "status_changed", f"Status set to {status}")

st.sidebar.title("Aegis")
page = st.sidebar.radio("Navigate", [
    "Dashboard", "AI Inventory", "Framework Crosswalk",
    "Risk & Control Assessments", "Incident Response",
    "Tasks & Remediation", "Audit Trail", "About & Sources"
])
st.sidebar.caption("Local prototype • SQLite • No external API required")

# Dashboard
if page == "Dashboard":
    st.title("Aegis AI Governance")
    st.caption("Framework-aware AI risk, controls and incident response")
    s = systems()
    i = incident_options()
    a = read_df("SELECT * FROM assessments")
    t = read_df("SELECT * FROM tasks")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("AI systems", len(s))
    c2.metric("Open incidents", int((i["status"] != "Closed").sum()) if not i.empty else 0)
    c3.metric("Failed control tests", int((a["status"] == "Fail").sum()) if not a.empty else 0)
    c4.metric("Open remediation tasks", int((t["status"] != "Done").sum()) if not t.empty else 0)
    st.subheader("Recent incidents")
    if i.empty:
        st.info("No incidents yet. Add a system, then create a simulated incident under Incident Response.")
    else:
        st.dataframe(i[["id","system_name","title","incident_type","severity","status","created_at"]].head(10),
                     use_container_width=True, hide_index=True)
    st.subheader("Control assessment status")
    if a.empty:
        st.info("No control assessments yet.")
    else:
        st.bar_chart(a["status"].value_counts())
    

# Inventory
elif page == "AI Inventory":
    st.title("AI System Inventory")
    with st.form("system_form", clear_on_submit=True):
        name = st.text_input("AI system name", placeholder="TalentScreen AI")
        owner = st.text_input("Accountable owner", placeholder="HR Technology Manager")
        purpose = st.text_area("Intended purpose", placeholder="Assist recruiters in screening applications")
        context = st.text_input("Deployment context", placeholder="Internal HR team; EU applicants")
        data_types = st.text_input("Data types processed", placeholder="CVs, work history, interview notes")
        risk = st.selectbox("Preliminary internal risk rating", ["Low","Medium","High","Critical"])
        classification = st.selectbox("EU AI Act classification assessment", [
            "Not assessed", "Potentially high-risk — requires assessment",
            "High-risk — assessed by reviewer", "Not high-risk — rationale documented",
            "Prohibited-practice concern — escalate for legal review"
        ])
        submit = st.form_submit_button("Register AI system")
        if submit:
            if not all([name.strip(), owner.strip(), purpose.strip(), context.strip(), data_types.strip()]):
                st.error("Complete all fields.")
            else:
                with db() as conn:
                    cur = conn.execute("""INSERT INTO ai_systems
                    (name, owner, purpose, deployment_context, data_types, preliminary_risk,
                     eu_ai_act_classification, created_at) VALUES (?,?,?,?,?,?,?,?)""",
                    (name.strip(), owner.strip(), purpose.strip(), context.strip(), data_types.strip(),
                     risk, classification, now()))
                    new_id = cur.lastrowid
                log_action("ai_system", new_id, "created", f"Registered {name}")
                st.success(f"Registered {name}.")
                st.rerun()
    st.subheader("Registered systems")
    data = systems()
    if data.empty:
        st.info("No systems registered yet.")
    else:
        st.dataframe(data.drop(columns=["created_at"]), use_container_width=True, hide_index=True)
        st.download_button("Download inventory CSV", data.to_csv(index=False).encode("utf-8"),
                           "ai_inventory.csv", "text/csv")

# Crosswalk
elif page == "Framework Crosswalk":
    st.title("EU AI Act ↔ NIST AI RMF Crosswalk")
    st.caption("Starter mapping for learning and review. A mapping is not proof of compliance or legal equivalence.")
    controls = read_df("SELECT * FROM framework_controls ORDER BY id")
    framework_filter = st.multiselect("Filter framework", sorted(controls["framework"].unique()),
                                      default=sorted(controls["framework"].unique()))
    view = controls[controls["framework"].isin(framework_filter)]
    for _, row in view.iterrows():
        with st.expander(f"{row['framework']} — {row['reference']}: {row['title']}"):
            st.markdown(f"**Summary:** {row['requirement_summary']}")
            st.markdown(f"**Related NIST function(s):** {row['nist_function']}")
            st.markdown(f"**Mapping rationale:** {row['mapping_rationale']}")
            st.markdown(f"**Applicability caveat:** {row['applicability_note']}")
            st.markdown(f"**Source:** {row['source_url']}")
    st.download_button("Download crosswalk CSV", controls.to_csv(index=False).encode("utf-8"),
                       "framework_crosswalk.csv", "text/csv")

# Assessments
elif page == "Risk & Control Assessments":
    st.title("Risk & Control Assessments")
    sys_df = systems()
    ctrl_df = control_options()
    if sys_df.empty:
        st.info("Register an AI system first.")
    else:
        sys_map = {f"{r['name']} (ID {r['id']})": int(r["id"]) for _,r in sys_df.iterrows()}
        ctrl_map = {f"{r['framework']} — {r['reference']}: {r['title']} (ID {r['id']})": int(r["id"]) for _,r in ctrl_df.iterrows()}
        with st.form("assessment_form", clear_on_submit=True):
            sys_label = st.selectbox("AI system", list(sys_map))
            ctrl_label = st.selectbox("Requirement / control", list(ctrl_map))
            status = st.selectbox("Test result", ["Not Tested","Pass","Fail","Needs Improvement","Not Applicable"])
            evidence = st.text_area("Evidence reference / test performed", placeholder="Test ID, document reference, date, result; avoid sensitive data")
            gap = st.text_area("Gap, limitation or rationale", placeholder="Required for Fail, Needs Improvement or Not Applicable")
            owner = st.text_input("Control owner", "AI Governance Lead")
            due = st.date_input("Remediation due date")
            save = st.form_submit_button("Save assessment")
            if save:
                with db() as conn:
                    cur = conn.execute("""INSERT INTO assessments
                    (system_id, control_id, status, evidence, gap, owner, due_date, assessed_at)
                    VALUES (?,?,?,?,?,?,?,?)""",
                    (sys_map[sys_label], ctrl_map[ctrl_label], status, evidence, gap, owner,
                     due.isoformat(), now()))
                    aid = cur.lastrowid
                log_action("assessment", aid, "created", f"{status}: {ctrl_label}")
                st.success("Assessment saved.")
                st.rerun()
    st.subheader("Assessment register")
    assessments = read_df("""SELECT a.id, s.name AS system, c.framework, c.reference, c.title,
        a.status, a.evidence, a.gap, a.owner, a.due_date, a.assessed_at
        FROM assessments a JOIN ai_systems s ON s.id=a.system_id
        JOIN framework_controls c ON c.id=a.control_id ORDER BY a.id DESC""")
    if assessments.empty:
        st.info("No assessments yet.")
    else:
        st.dataframe(assessments, use_container_width=True, hide_index=True)
        st.download_button("Download assessment CSV", assessments.to_csv(index=False).encode("utf-8"),
                           "control_assessments.csv", "text/csv")

# Incident response
elif page == "Incident Response":
    st.title("Incident Response")
    sys_df = systems()
    if sys_df.empty:
        st.info("Register an AI system before creating an incident.")
    else:
        sys_map = {f"{r['name']} (ID {r['id']})": int(r["id"]) for _,r in sys_df.iterrows()}
        with st.form("incident_form", clear_on_submit=True):
            sys_label = st.selectbox("Affected AI system", list(sys_map))
            title = st.text_input("Incident title", placeholder="Unexpected disparity in candidate rankings")
            itype = st.selectbox("Incident type", [
                "Bias / discriminatory outcome", "Sensitive data disclosure", "Prompt injection",
                "Unauthorized tool or data access", "Reliability / model drift",
                "Cybersecurity compromise", "Other"
            ])
            description = st.text_area("What happened?", placeholder="Facts observed; separate confirmed facts from hypotheses. Do not enter real personal data.")
            severity = st.selectbox("Initial triage severity", ["Low","Medium","High","Critical"])
            impact = st.text_area("Known or potential impact", placeholder="Affected users, decisions, systems, data; mark unknowns")
            containment = st.text_area("Containment actions / recommendations", placeholder="What has been done? What should an authorized responder consider?")
            create = st.form_submit_button("Create incident")
            if create:
                if not title.strip() or not description.strip():
                    st.error("Title and description are required.")
                else:
                    with db() as conn:
                        cur = conn.execute("""INSERT INTO incidents
                        (system_id,title,incident_type,description,severity,status,impact,containment,root_cause,created_at,updated_at)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (sys_map[sys_label], title.strip(), itype, description.strip(), severity,
                         "Open", impact.strip(), containment.strip(), "", now(), now()))
                        iid = cur.lastrowid
                    log_action("incident", iid, "created", f"{severity} {itype}: {title}")
                    st.success(f"Incident IR-{iid:04d} created.")
                    st.rerun()
    incidents = incident_options()
    st.subheader("Incident register")
    if incidents.empty:
        st.info("No incidents recorded.")
    else:
        st.dataframe(incidents[["id","system_name","title","incident_type","severity","status","created_at"]],
                     use_container_width=True, hide_index=True)
        st.subheader("Investigate and update an incident")
        imap = {f"IR-{int(r['id']):04d} — {r['title']}": int(r["id"]) for _,r in incidents.iterrows()}
        selected = st.selectbox("Select incident", list(imap))
        row = incidents[incidents["id"] == imap[selected]].iloc[0]
        with st.form("update_incident"):
            status = st.selectbox("Status", ["Open","Investigating","Contained","Remediation","Monitoring","Closed"],
                                  index=["Open","Investigating","Contained","Remediation","Monitoring","Closed"].index(row["status"]))
            root = st.text_area("Root-cause findings", value=row["root_cause"] or "")
            impact = st.text_area("Impact assessment", value=row["impact"] or "")
            containment = st.text_area("Containment / response record", value=row["containment"] or "")
            update = st.form_submit_button("Update incident")
            if update:
                with db() as conn:
                    conn.execute("""UPDATE incidents SET status=?,root_cause=?,impact=?,containment=?,updated_at=?
                                    WHERE id=?""",
                                 (status,root,impact,containment,now(),int(row["id"])))
                log_action("incident", int(row["id"]), "updated", f"Status={status}; response record updated")
                st.success("Incident updated and audit event recorded.")
                st.rerun()
        st.subheader("Suggested response checklist")
        playbooks = {
            "Bias / discriminatory outcome": [
                "Preserve model/version and evaluation dataset references",
                "Validate the finding with appropriate statistical tests",
                "Assess affected people and decisions",
                "Consider pausing or restricting the affected decision workflow",
                "Assign remediation owner and define retest criteria",
                "Record human approval before resuming affected use"
            ],
            "Sensitive data disclosure": [
                "Restrict the affected data path or feature if warranted",
                "Preserve protected evidence and redact routine logs",
                "Determine data types, recipients and scope",
                "Escalate to security, privacy and legal owners",
                "Assess applicable notification obligations with qualified reviewers",
                "Verify fix and monitor recurrence"
            ],
            "Prompt injection": [
                "Preserve prompt, retrieved content and tool-call evidence safely",
                "Check whether any unauthorized tool action succeeded",
                "Disable or restrict risky tool permissions where warranted",
                "Patch retrieval, instruction handling or authorization controls",
                "Retest with benign and adversarial cases",
                "Approve recovery and monitor"
            ],
            "Unauthorized tool or data access": [
                "Revoke or restrict the affected credential/permission if warranted",
                "Preserve access logs and relevant request identifiers",
                "Establish scope of accessed resources",
                "Rotate exposed secrets if applicable",
                "Test authorization boundaries",
                "Approve restoration after verification"
            ],
            "Reliability / model drift": [
                "Identify model, prompt, data and configuration versions",
                "Compare results against a baseline evaluation set",
                "Assess impact on decisions and users",
                "Consider rollback or human review",
                "Retest against acceptance criteria",
                "Document release approval and ongoing monitoring"
            ],
            "Cybersecurity compromise": [
                "Activate the organization's security incident process",
                "Contain affected systems and credentials as authorized",
                "Preserve logs and forensic evidence",
                "Determine scope and possible data exposure",
                "Remediate root cause and validate recovery",
                "Record lessons learned and preventive actions"
            ],
            "Other": [
                "Preserve relevant evidence",
                "Determine scope and impact",
                "Assign incident owner",
                "Document containment and investigation",
                "Define remediation and verification criteria",
                "Record closure approval and lessons learned"
            ],
        }
        for item in playbooks.get(row["incident_type"], playbooks["Other"]):
            st.checkbox(item, key=f"pb_{row['id']}_{item}")
        st.caption("Checklist items are suggestions; responders must tailor them to the facts and approved procedures.")
        st.subheader("Create remediation task")
        with st.form("task_form", clear_on_submit=True):
            task_text = st.text_input("Task description")
            task_owner = st.text_input("Assigned owner")
            task_due = st.date_input("Task due date")
            task_notes = st.text_area("Acceptance criteria / notes")
            add_task = st.form_submit_button("Add task to this incident")
            if add_task:
                if task_text.strip() and task_owner.strip():
                    with db() as conn:
                        cur = conn.execute("""INSERT INTO tasks
                        (incident_id,task,owner,status,due_date,notes,created_at)
                        VALUES (?,?,?,?,?,?,?)""",
                        (int(row["id"]),task_text.strip(),task_owner.strip(),"Open",
                         task_due.isoformat(),task_notes.strip(),now()))
                        tid = cur.lastrowid
                    log_action("task", tid, "created", f"Incident IR-{int(row['id']):04d}: {task_text}")
                    st.success("Remediation task created.")
                    st.rerun()
                else:
                    st.error("Task description and owner are required.")
        report = f"""# Incident Report — IR-{int(row['id']):04d}

- **AI system:** {row['system_name']}
- **Title:** {row['title']}
- **Type:** {row['incident_type']}
- **Severity:** {row['severity']}
- **Status:** {row['status']}
- **Created:** {row['created_at']}
- **Last updated:** {row['updated_at']}

## Description
{row['description']}

## Impact assessment
{row['impact'] or 'Not documented'}

## Containment / response record
{row['containment'] or 'Not documented'}

## Root-cause findings
{row['root_cause'] or 'Not documented'}

## Governance note
This report records the current application entries. It does not determine legal reportability or establish compliance. Obtain appropriate legal, privacy and security review where needed.
"""
        st.download_button("Download selected incident report (Markdown)",
                           report.encode("utf-8"), f"incident_IR-{int(row['id']):04d}.md",
                           "text/markdown")

# Tasks
elif page == "Tasks & Remediation":
    st.title("Tasks & Remediation")
    tasks = read_df("""SELECT t.id, t.incident_id, i.title AS incident, t.task, t.owner,
                       t.status, t.due_date, t.notes, t.created_at
                       FROM tasks t JOIN incidents i ON i.id=t.incident_id
                       ORDER BY t.id DESC""")
    if tasks.empty:
        st.info("No tasks yet. Create a task from an incident.")
    else:
        st.dataframe(tasks, use_container_width=True, hide_index=True)
        task_map = {f"Task {int(r['id'])}: {r['task']}": int(r['id']) for _,r in tasks.iterrows()}
        selected = st.selectbox("Update task", list(task_map))
        tid = task_map[selected]
        taskrow = tasks[tasks["id"] == tid].iloc[0]
        with st.form("task_update"):
            status = st.selectbox("Task status", ["Open","In Progress","Blocked","Done"],
                                  index=["Open","In Progress","Blocked","Done"].index(taskrow["status"]))
            notes = st.text_area("Notes / verification evidence", value=taskrow["notes"] or "")
            update = st.form_submit_button("Save task update")
            if update:
                with db() as conn:
                    conn.execute("UPDATE tasks SET status=?, notes=? WHERE id=?", (status,notes,tid))
                log_action("task", tid, "updated", f"Status={status}; notes updated")
                st.success("Task updated.")
                st.rerun()
        st.download_button("Download tasks CSV", tasks.to_csv(index=False).encode("utf-8"),
                           "remediation_tasks.csv", "text/csv")

# Audit
elif page == "Audit Trail":
    st.title("Audit Trail")
    audit = read_df("SELECT * FROM audit_log ORDER BY id DESC")
    st.caption("This is an application activity log, not a tamper-proof or independently validated audit system.")
    if audit.empty:
        st.info("No activity recorded yet.")
    else:
        st.dataframe(audit, use_container_width=True, hide_index=True)
        st.download_button("Download audit trail CSV", audit.to_csv(index=False).encode("utf-8"),
                           "audit_trail.csv", "text/csv")

# About
elif page == "About & Sources":
    st.title("About Aegis AI Governance")
    st.markdown("""
    **Purpose:** Educational prototype for connecting AI governance requirements, risk assessment,
    control testing, incident response and remediation tracking.

    **Frameworks and official sources**
    - [EU AI Act — Regulation (EU) 2024/1689](https://eur-lex.europa.eu/eli/reg/2024/1689/oj)
    - [European Commission AI Act Service Desk](https://ai-act-service-desk.ec.europa.eu/en/ai-act-explorer)
    - [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
    - [NIST AI RMF Playbook](https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook)
    - [NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)

    **Important limitations**
    - Crosswalks are working mappings for learning and should be reviewed by qualified personnel.
    - The application does not automatically decide whether an AI system is legally high-risk or whether an incident is reportable.
    - Risk ratings and incident severities are organization-defined and require documented criteria.
    - Do not enter real personal, confidential or regulated data into this demo.
    - The local SQLite database and activity log are not hardened for production use.
    """)
    st.subheader("Export project data")
    for table, filename in [
        ("ai_systems","ai_systems.csv"),
        ("framework_controls","framework_controls.csv"),
        ("assessments","assessments.csv"),
        ("incidents","incidents.csv"),
        ("tasks","tasks.csv"),
        ("audit_log","audit_log.csv"),
    ]:
        df = read_df(f"SELECT * FROM {table}")
        st.download_button(f"Export {table}", df.to_csv(index=False).encode("utf-8"),
                           filename, "text/csv", key=f"export_{table}")
