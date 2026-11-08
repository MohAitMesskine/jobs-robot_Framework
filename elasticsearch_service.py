import os
import json
import logging
import requests

logger = logging.getLogger(__name__)

INDEX_NAME = "jobs"

def get_es_url():
    return os.environ.get("ELASTICSEARCH_URL", "http://127.0.0.1:9200").rstrip("/")

def is_es_available():
    url = get_es_url()
    try:
        response = requests.get(url, timeout=1.0)
        return response.status_code == 200
    except Exception:
        return False

def init_es_index():
    """Ensure index exists with proper mappings."""
    if not is_es_available():
        return False
    url = f"{get_es_url()}/{INDEX_NAME}"
    try:
        head_res = requests.head(url, timeout=1.5)
        if head_res.status_code == 200:
            return True

        mapping = {
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "title": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "company": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                    "location": {"type": "keyword", "fields": {"text": {"type": "text"}}},
                    "contract": {"type": "keyword"},
                    "salary": {"type": "text"},
                    "description": {"type": "text"},
                    "tags": {"type": "keyword", "fields": {"text": {"type": "text"}}}
                }
            }
        }
        res = requests.put(url, json=mapping, headers={"Content-Type": "application/json"}, timeout=2.0)
        return res.status_code in (200, 201)
    except Exception as exc:
        logger.warning("Error initializing Elasticsearch index: %s", exc)
        return False

def index_job(job):
    """Index a single job document."""
    if not is_es_available():
        return False
    init_es_index()
    url = f"{get_es_url()}/{INDEX_NAME}/_doc/{job['id']}"
    try:
        res = requests.put(url, json=job, headers={"Content-Type": "application/json"}, timeout=1.5)
        return res.status_code in (200, 201)
    except Exception as exc:
        logger.warning("Error indexing job %s: %s", job.get("id"), exc)
        return False

def bulk_index_jobs(jobs):
    """Index a list of jobs."""
    if not is_es_available() or not jobs:
        return False
    init_es_index()
    url = f"{get_es_url()}/_bulk"
    lines = []
    for job in jobs:
        lines.append(json.dumps({"index": {"_index": INDEX_NAME, "_id": str(job["id"])}}))
        lines.append(json.dumps(job))
    payload = "\n".join(lines) + "\n"
    try:
        res = requests.post(url, data=payload, headers={"Content-Type": "application/x-ndjson"}, timeout=3.0)
        return res.status_code in (200, 201)
    except Exception as exc:
        logger.warning("Error in bulk indexing jobs: %s", exc)
        return False

def delete_job_from_es(job_id):
    """Delete a job from ES."""
    if not is_es_available():
        return False
    url = f"{get_es_url()}/{INDEX_NAME}/_doc/{job_id}"
    try:
        res = requests.delete(url, timeout=1.5)
        return res.status_code in (200, 404)
    except Exception as exc:
        logger.warning("Error deleting job %s from ES: %s", job_id, exc)
        return False

def search_jobs_es(query="", location="", contract=""):
    """
    Search jobs in Elasticsearch.
    Returns (hits_list, True) on success, or ([], False) on error/unavailable.
    """
    if not is_es_available():
        return [], False

    must_clauses = []
    filter_clauses = []

    if query:
        must_clauses.append({
            "multi_match": {
                "query": query,
                "fields": ["title^3", "company^2", "tags^2", "description"],
                "fuzziness": "AUTO",
                "prefix_length": 2
            }
        })

    if location:
        filter_clauses.append({
            "wildcard": {
                "location": {
                    "value": f"*{location.lower()}*",
                    "case_insensitive": True
                }
            }
        })

    if contract:
        filter_clauses.append({
            "term": {
                "contract": contract.upper()
            }
        })

    bool_query = {}
    if must_clauses:
        bool_query["must"] = must_clauses
    else:
        bool_query["must"] = [{"match_all": {}}]

    if filter_clauses:
        bool_query["filter"] = filter_clauses

    es_query = {
        "query": {"bool": bool_query},
        "size": 100
    }

    url = f"{get_es_url()}/{INDEX_NAME}/_search"
    try:
        res = requests.post(url, json=es_query, headers={"Content-Type": "application/json"}, timeout=2.0)
        if res.status_code != 200:
            return [], False
        data = res.json()
        hits = [hit["_source"] for hit in data.get("hits", {}).get("hits", [])]
        return hits, True
    except Exception as exc:
        logger.warning("Error during Elasticsearch search: %s", exc)
        return [], False

def local_search_jobs(jobs, query="", location="", contract=""):
    """Fallback search implementation for local records."""
    q_clean = query.strip().casefold()
    loc_clean = location.strip().casefold()
    contract_clean = contract.strip().casefold()

    matches = []
    for job in jobs:
        searchable_text = " ".join([
            job.get("title", ""),
            job.get("company", ""),
            job.get("description", ""),
            *job.get("tags", []),
        ]).casefold()

        if q_clean and q_clean not in searchable_text:
            continue
        if loc_clean and loc_clean not in job.get("location", "").casefold():
            continue
        if contract_clean and contract_clean != job.get("contract", "").casefold():
            continue
        matches.append(job)
    return matches

