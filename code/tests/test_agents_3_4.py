import pytest
import asyncio
import os
import time
import tempfile
import numpy as np

from code.core.config import REPO_ROOT
from code.core.precheck import precheck_image
from code.agents.evidence_requirement import EvidenceRequirementAgent
from code.agents.vision_evidence import VisionEvidenceAgent
from code.agents.image_quality import ImageQualityAgent
from code.core.models import ImageFindings, ImageQuality, EvidenceRequirement

SKIP_VLM = not os.getenv("OPENROUTER_API_KEY")


def _make_valid_image():
    tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
    img = np.zeros((200, 300, 3), dtype=np.uint8)
    img[50:150, 50:250] = [100, 150, 200]
    import cv2
    cv2.imwrite(tmp.name, img)
    tmp.close()
    return tmp.name


async def analyze_images(image_paths, claim_object, claimed_issue, claimed_part):
    va = VisionEvidenceAgent()
    qa = ImageQualityAgent()
    findings = []
    quality = []
    for i, path in enumerate(image_paths):
        precheck = precheck_image(path)
        if not precheck["valid"]:
            q = ImageQuality(
                image_id=f"img_{i+1}",
                valid=False,
                blurry=True,
                confidence=1.0,
            )
            f = ImageFindings(
                image_id=f"img_{i+1}",
                object_visible=False,
                confidence=0.0,
            )
        else:
            f, q = await asyncio.gather(
                va.run(path, claim_object, claimed_issue, claimed_part),
                qa.run(path),
            )
        findings.append(f)
        quality.append(q)
    return findings, quality


class TestEvidenceRequirementAgent:
    def test_evidence_requirement_lookup(self):
        agent = EvidenceRequirementAgent()
        result = agent.lookup("car", "dent")
        assert isinstance(result, EvidenceRequirement)
        assert result.object_type == "car"
        assert result.issue_type == "dent"
        assert result.minimum_image_evidence != ""
        assert result.applies_to != ""

    def test_evidence_requirement_fuzzy_fallback(self):
        agent = EvidenceRequirementAgent()
        result = agent.lookup("car", "paint scratch")
        assert isinstance(result, EvidenceRequirement)
        assert result.object_type == "car"

    def test_evidence_requirement_unknown_passthrough(self):
        agent = EvidenceRequirementAgent()
        result = agent.lookup("car", "nonexistent_issue_type")
        assert isinstance(result, EvidenceRequirement)
        assert result.minimum_image_evidence != ""


class TestPrecheck:
    def test_cost_aware_routing_accepts_valid(self):
        import cv2
        path = _make_valid_image()
        try:
            result = precheck_image(path)
            assert result["valid"] is True
            assert result["reason"] == "passed"
            assert "dimensions" in result
        finally:
            os.unlink(path)

    def test_cost_aware_routing_skips_corrupt(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"not an image file")
            corrupt_path = f.name
        try:
            result = precheck_image(corrupt_path)
            assert result["valid"] is False
            assert result["reason"] == "corrupt_or_unreadable"
        finally:
            os.unlink(corrupt_path)

    def test_cost_aware_routing_skips_too_small(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            import numpy as np
            import cv2
            small_img = np.zeros((32, 32, 3), dtype=np.uint8)
            cv2.imwrite(f.name, small_img)
            small_path = f.name
        try:
            result = precheck_image(small_path)
            assert result["valid"] is False
            assert result["reason"] == "too_small"
        finally:
            os.unlink(small_path)


class TestCostAwareRoutingIntegration:
    def test_cost_aware_routing_integration(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(b"garbage data")
            corrupt = f.name
        corrupt_paths = [corrupt]
        try:
            loop = asyncio.new_event_loop()
            findings, quality = loop.run_until_complete(
                analyze_images(corrupt_paths, "car", "dent", "front_bumper")
            )
            loop.close()
            assert len(findings) == 1
            assert len(quality) == 1
            assert findings[0].object_visible is False
            assert findings[0].confidence == 0.0
            assert quality[0].valid is False
            assert quality[0].confidence == 1.0
        finally:
            os.unlink(corrupt)


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_VLM, reason="OPENROUTER_API_KEY not set")
async def test_vision_agent_returns_valid_struct():
    path = _make_valid_image()
    try:
        agent = VisionEvidenceAgent()
        result = await agent.run(path, "car", "dent", "front_bumper")
        assert isinstance(result, ImageFindings)
        assert isinstance(result.object_visible, bool)
        assert isinstance(result.visible_parts, list)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
        assert result.issue_severity in ("none", "low", "medium", "high", "unknown")
    finally:
        os.unlink(path)


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_VLM, reason="OPENROUTER_API_KEY not set")
async def test_quality_agent_returns_valid_struct():
    path = _make_valid_image()
    try:
        agent = ImageQualityAgent()
        result = await agent.run(path)
        assert isinstance(result, ImageQuality)
        assert isinstance(result.blurry, bool)
        assert isinstance(result.cropped_or_obstructed, bool)
        assert isinstance(result.low_light_or_glare, bool)
        assert isinstance(result.wrong_angle, bool)
        assert isinstance(result.wrong_object, bool)
        assert isinstance(result.possible_manipulation, bool)
        assert isinstance(result.non_original_image, bool)
        assert isinstance(result.text_instruction_present, bool)
        assert isinstance(result.valid, bool)
        assert isinstance(result.confidence, float)
        assert 0.0 <= result.confidence <= 1.0
    finally:
        os.unlink(path)


@pytest.mark.asyncio
@pytest.mark.skipif(SKIP_VLM, reason="OPENROUTER_API_KEY not set")
async def test_parallel_execution():
    path = _make_valid_image()
    try:
        va = VisionEvidenceAgent()
        qa = ImageQualityAgent()
        t0 = time.time()
        f, q = await asyncio.gather(
            va.run(path, "car", "dent", "front_bumper"),
            qa.run(path),
        )
        elapsed = time.time() - t0
        assert isinstance(f, ImageFindings)
        assert isinstance(q, ImageQuality)
        assert elapsed < 60
    finally:
        os.unlink(path)
