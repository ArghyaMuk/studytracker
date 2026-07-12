"""Seed script for Curriculum Service with example B.Tech CSE data.

Run after services are up:
    python scripts/seed_curriculum.py

This demonstrates the program-agnostic setup pattern from section 7.
"""

import httpx
import asyncio

BASE_URL = "http://localhost:8000/api/v1"  # Through API Gateway


async def seed():
    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Create program
        program_resp = await client.post(
            f"{BASE_URL}/admin/programs",
            json={"name": "B.Tech CSE", "total_semesters": 8},
        )
        if program_resp.status_code == 201:
            program = program_resp.json()
            program_id = program["id"]
            print(f"Created program: {program['name']} (id={program_id})")
        else:
            print(f"Program creation failed: {program_resp.text}")
            return

        # 2. Add subjects for Semester 3
        subjects = [
            {
                "code": "CS301",
                "name": "Data Structures & Algorithms",
                "semester": 3,
                "type": "theory",
                "credits": 4,
                "units": [
                    {"unit_number": 1, "unit_title": "Arrays, Linked Lists & Stacks", "topics_json": '["arrays","linked-lists","stacks","queues"]'},
                    {"unit_number": 2, "unit_title": "Trees & Graphs", "topics_json": '["binary-trees","BST","graphs","BFS","DFS"]'},
                    {"unit_number": 3, "unit_title": "Sorting & Searching", "topics_json": '["merge-sort","quick-sort","binary-search","hashing"]'},
                    {"unit_number": 4, "unit_title": "Dynamic Programming & Greedy", "topics_json": '["DP","memoization","greedy-algorithms","backtracking"]'},
                ],
            },
            {
                "code": "CS302",
                "name": "Database Management Systems",
                "semester": 3,
                "type": "theory",
                "credits": 3,
                "units": [
                    {"unit_number": 1, "unit_title": "ER Model & Relational Algebra", "topics_json": '["ER-diagrams","relational-model","normalization"]'},
                    {"unit_number": 2, "unit_title": "SQL & Query Processing", "topics_json": '["SQL","joins","subqueries","indexing"]'},
                    {"unit_number": 3, "unit_title": "Transactions & Concurrency", "topics_json": '["ACID","locking","deadlocks","recovery"]'},
                    {"unit_number": 4, "unit_title": "NoSQL & Distributed DBs", "topics_json": '["NoSQL","CAP-theorem","sharding","replication"]'},
                ],
            },
            {
                "code": "CS303",
                "name": "Operating Systems",
                "semester": 3,
                "type": "theory",
                "credits": 3,
                "units": [
                    {"unit_number": 1, "unit_title": "Process Management", "topics_json": '["processes","threads","scheduling","synchronization"]'},
                    {"unit_number": 2, "unit_title": "Memory Management", "topics_json": '["paging","segmentation","virtual-memory","page-replacement"]'},
                    {"unit_number": 3, "unit_title": "File Systems & I/O", "topics_json": '["file-systems","disk-scheduling","I/O-management"]'},
                    {"unit_number": 4, "unit_title": "Deadlocks & Security", "topics_json": '["deadlocks","detection","prevention","OS-security"]'},
                ],
            },
            {
                "code": "CS304",
                "name": "DSA Lab",
                "semester": 3,
                "type": "lab",
                "credits": 2,
                "units": [
                    {"unit_number": 1, "unit_title": "Implementation of Data Structures", "topics_json": '["linked-list-impl","stack-impl","queue-impl","tree-impl"]'},
                ],
            },
        ]

        for subject_data in subjects:
            resp = await client.post(
                f"{BASE_URL}/admin/programs/{program_id}/subjects",
                json=subject_data,
            )
            if resp.status_code == 201:
                subj = resp.json()
                print(f"  Added subject: {subj['code']} - {subj['name']} ({len(subj.get('units', []))} units)")
            else:
                print(f"  Failed to add {subject_data['code']}: {resp.text}")

    print("\nSeed complete! Curriculum data ready.")


if __name__ == "__main__":
    asyncio.run(seed())
