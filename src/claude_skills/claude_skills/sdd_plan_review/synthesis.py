#!/usr/bin/env python3
"""
Multi-model response synthesis for spec reviews.

Parses AI tool responses, extracts structured data, builds consensus,
and generates overall recommendations.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from statistics import mean, median


def parse_response(tool_output: str, tool_name: str) -> Dict[str, Any]:
    """
    Parse AI tool response into structured format.

    Tries multiple parsing strategies:
    1. Extract JSON from code blocks
    2. Extract JSON from raw text
    3. Regex extraction of key fields
    4. Return error with raw output

    Args:
        tool_output: Raw output from AI tool
        tool_name: Name of the tool for logging

    Returns:
        Parsed response dictionary
    """
    result = {
        "success": False,
        "tool": tool_name,
        "raw_output": tool_output,
        "parsed_data": None,
        "error": None,
    }

    # Strategy 1: Extract JSON from code blocks
    json_match = re.search(r'```json\s*(\{.+?\})\s*```', tool_output, re.DOTALL)
    if json_match:
        try:
            data = json.loads(json_match.group(1))
            result["success"] = True
            result["parsed_data"] = normalize_response(data, tool_name)
            return result
        except json.JSONDecodeError as e:
            result["error"] = f"JSON in code block invalid: {str(e)}"

    # Strategy 2: Extract JSON from raw text
    try:
        # Try to find JSON object in output
        start = tool_output.find('{')
        end = tool_output.rfind('}') + 1
        if start != -1 and end > start:
            json_str = tool_output[start:end]
            data = json.loads(json_str)
            result["success"] = True
            result["parsed_data"] = normalize_response(data, tool_name)
            return result
    except (json.JSONDecodeError, ValueError) as e:
        result["error"] = f"No valid JSON found: {str(e)}"

    # Strategy 3: Regex extraction (fallback)
    try:
        data = extract_with_regex(tool_output)
        if data:
            result["success"] = True
            result["parsed_data"] = normalize_response(data, tool_name)
            return result
    except Exception as e:
        result["error"] = f"Regex extraction failed: {str(e)}"

    # All strategies failed
    result["error"] = result.get("error") or "Could not parse response"
    return result


def extract_with_regex(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract structured data using regex patterns.

    Args:
        text: Raw text to parse

    Returns:
        Extracted data dictionary or None
    """
    data = {
        "overall_score": None,
        "dimensions": {},
        "issues": [],
        "strengths": [],
        "recommendations": [],
        "recommendation": None,
    }

    # Extract overall score
    score_match = re.search(r'overall[_\s]score["\s:]+(\d+(?:\.\d+)?)', text, re.IGNORECASE)
    if score_match:
        data["overall_score"] = float(score_match.group(1))

    # Extract recommendation
    rec_match = re.search(r'recommendation["\s:]+([A-Z]+)', text)
    if rec_match:
        data["recommendation"] = rec_match.group(1)

    # If we got at least overall score, consider it a partial success
    if data["overall_score"] is not None:
        return data

    return None


def normalize_response(data: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
    """
    Normalize and validate response data.

    Args:
        data: Raw parsed data
        tool_name: Tool name for context

    Returns:
        Normalized response
    """
    normalized = {
        "tool": tool_name,
        "overall_score": None,
        "dimensions": {},
        "issues": [],
        "strengths": [],
        "recommendations": [],
        "recommendation": None,
    }

    # Normalize overall score
    if "overall_score" in data:
        score = data["overall_score"]
        if isinstance(score, (int, float)):
            normalized["overall_score"] = max(1, min(10, float(score)))

    # Normalize dimensions
    if "dimensions" in data and isinstance(data["dimensions"], dict):
        for dim_name, dim_data in data["dimensions"].items():
            if isinstance(dim_data, dict) and "score" in dim_data:
                score = dim_data["score"]
                if isinstance(score, (int, float)):
                    normalized["dimensions"][dim_name] = {
                        "score": max(1, min(10, float(score))),
                        "notes": dim_data.get("notes", "")
                    }

    # Normalize issues
    if "issues" in data and isinstance(data["issues"], list):
        for issue in data["issues"]:
            if isinstance(issue, dict):
                normalized_issue = {
                    "severity": normalize_severity(issue.get("severity", "MEDIUM")),
                    "title": issue.get("title", "Untitled issue"),
                    "description": issue.get("description", ""),
                    "impact": issue.get("impact", ""),
                    "recommendation": issue.get("recommendation", ""),
                }
                normalized["issues"].append(normalized_issue)

    # Normalize strengths
    if "strengths" in data and isinstance(data["strengths"], list):
        normalized["strengths"] = [str(s) for s in data["strengths"] if s]

    # Normalize recommendations
    if "recommendations" in data and isinstance(data["recommendations"], list):
        normalized["recommendations"] = [str(r) for r in data["recommendations"] if r]

    # Normalize overall recommendation
    if "recommendation" in data:
        rec = str(data["recommendation"]).upper()
        if rec in ["APPROVE", "REVISE", "REJECT"]:
            normalized["recommendation"] = rec
        elif normalized["overall_score"]:
            # Infer from score
            if normalized["overall_score"] >= 8:
                normalized["recommendation"] = "APPROVE"
            elif normalized["overall_score"] >= 5:
                normalized["recommendation"] = "REVISE"
            else:
                normalized["recommendation"] = "REJECT"

    return normalized


def normalize_severity(severity: str) -> str:
    """Normalize severity to standard values."""
    severity = str(severity).upper()
    valid = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    if severity in valid:
        return severity
    # Map common variations
    if "CRIT" in severity or "BLOCKER" in severity:
        return "CRITICAL"
    if "HIGH" in severity or "MAJOR" in severity:
        return "HIGH"
    if "LOW" in severity or "MINOR" in severity:
        return "LOW"
    return "MEDIUM"


def build_consensus(responses: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build consensus from multiple model responses.

    Args:
        responses: List of normalized response dictionaries

    Returns:
        Consensus dictionary with aggregated scores and recommendations
    """
    if not responses:
        return {
            "success": False,
            "error": "No valid responses to synthesize",
        }

    consensus = {
        "success": True,
        "num_models": len(responses),
        "models": [r["tool"] for r in responses],
        "overall_score": None,
        "overall_score_avg": None,
        "overall_score_median": None,
        "dimension_scores": {},
        "all_issues": [],
        "all_strengths": [],
        "all_recommendations": [],
        "final_recommendation": None,
        "consensus_level": None,
        "agreements": [],
        "disagreements": [],
    }

    # Aggregate overall scores
    scores = [r["overall_score"] for r in responses if r["overall_score"] is not None]
    if scores:
        consensus["overall_score_avg"] = round(mean(scores), 1)
        consensus["overall_score_median"] = round(median(scores), 1)
        consensus["overall_score"] = consensus["overall_score_avg"]

    # Aggregate dimension scores
    all_dimensions = set()
    for r in responses:
        all_dimensions.update(r["dimensions"].keys())

    for dim in all_dimensions:
        dim_scores = []
        for r in responses:
            if dim in r["dimensions"]:
                dim_scores.append(r["dimensions"][dim]["score"])

        if dim_scores:
            consensus["dimension_scores"][dim] = {
                "avg": round(mean(dim_scores), 1),
                "median": round(median(dim_scores), 1),
                "min": min(dim_scores),
                "max": max(dim_scores),
                "count": len(dim_scores),
            }

    # Aggregate issues (with deduplication)
    consensus["all_issues"] = aggregate_issues(responses)

    # Aggregate strengths and recommendations
    for r in responses:
        consensus["all_strengths"].extend(r["strengths"])
        consensus["all_recommendations"].extend(r["recommendations"])

    # Deduplicate strengths/recommendations
    consensus["all_strengths"] = list(set(consensus["all_strengths"]))
    consensus["all_recommendations"] = list(set(consensus["all_recommendations"]))

    # Determine final recommendation
    recommendations = [r["recommendation"] for r in responses if r["recommendation"]]
    if recommendations:
        # Count votes
        votes = {"APPROVE": 0, "REVISE": 0, "REJECT": 0}
        for rec in recommendations:
            if rec in votes:
                votes[rec] += 1

        # Majority wins, bias toward caution (REVISE > APPROVE, REJECT > REVISE)
        if votes["REJECT"] > 0:
            consensus["final_recommendation"] = "REJECT"
        elif votes["REVISE"] > votes["APPROVE"]:
            consensus["final_recommendation"] = "REVISE"
        elif votes["APPROVE"] > 0:
            consensus["final_recommendation"] = "APPROVE"
        else:
            consensus["final_recommendation"] = "REVISE"  # default to caution

    # Calculate consensus level
    consensus["consensus_level"] = calculate_consensus_level(responses)

    # Identify agreements and disagreements
    consensus["agreements"], consensus["disagreements"] = identify_agreements(responses)

    return consensus


def aggregate_issues(responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Aggregate and deduplicate issues from all models.

    Args:
        responses: List of model responses

    Returns:
        Deduplicated list of issues with model attribution
    """
    all_issues = []
    seen_titles = {}

    for response in responses:
        for issue in response["issues"]:
            title = issue["title"].lower().strip()

            # Check if similar issue already exists
            if title in seen_titles:
                # Add model to existing issue
                existing = seen_titles[title]
                existing["flagged_by"].append(response["tool"])
            else:
                # New issue
                new_issue = issue.copy()
                new_issue["flagged_by"] = [response["tool"]]
                all_issues.append(new_issue)
                seen_titles[title] = new_issue

    # Sort by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    all_issues.sort(key=lambda x: (
        severity_order.get(x["severity"], 4),
        -len(x["flagged_by"])  # More models = higher priority
    ))

    return all_issues


def calculate_consensus_level(responses: List[Dict[str, Any]]) -> str:
    """
    Calculate consensus level based on score variance.

    Args:
        responses: List of model responses

    Returns:
        Consensus level string
    """
    scores = [r["overall_score"] for r in responses if r["overall_score"] is not None]

    if len(scores) < 2:
        return "single_model"

    # Calculate standard deviation
    avg = mean(scores)
    variance = sum((x - avg) ** 2 for x in scores) / len(scores)
    std_dev = variance ** 0.5

    # Classify consensus
    if std_dev < 1.0:
        return "strong"
    elif std_dev < 2.0:
        return "moderate"
    elif std_dev < 3.0:
        return "weak"
    else:
        return "conflicted"


def identify_agreements(responses: List[Dict[str, Any]]) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Identify points of agreement and disagreement.

    Args:
        responses: List of model responses

    Returns:
        Tuple of (agreements list, disagreements list)
    """
    agreements = []
    disagreements = []

    # Check recommendation agreement
    recommendations = [r["recommendation"] for r in responses if r["recommendation"]]
    if recommendations:
        unique_recs = set(recommendations)
        if len(unique_recs) == 1:
            agreements.append(f"All models recommend: {recommendations[0]}")
        else:
            rec_counts = {rec: recommendations.count(rec) for rec in unique_recs}
            disagreements.append({
                "topic": "Overall Recommendation",
                "positions": rec_counts,
                "description": "Models disagree on whether to approve, revise, or reject",
            })

    # Check score agreement
    scores = [r["overall_score"] for r in responses if r["overall_score"] is not None]
    if scores:
        score_range = max(scores) - min(scores)
        if score_range <= 1.5:
            agreements.append(f"Scores closely aligned (range: {score_range:.1f})")
        elif score_range >= 4.0:
            disagreements.append({
                "topic": "Overall Score",
                "positions": {r["tool"]: r["overall_score"] for r in responses if r["overall_score"]},
                "description": f"Wide score variation (range: {score_range:.1f})",
            })

    return agreements, disagreements
