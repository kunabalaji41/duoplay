import base64
import json


def _decode_segment(segment):
    padding = "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(segment + padding))


def verify_jwt(token, expected_audience):
    header_segment, payload_segment, signature_segment = token.split(".")
    header = _decode_segment(header_segment)
    payload = _decode_segment(payload_segment)

    algorithm = header.get("alg")
    if algorithm is None or algorithm.lower() == "none":
        raise PermissionError("unsigned tokens are not accepted")

    if not signature_segment:
        raise PermissionError("missing signature")

    if payload.get("aud") != expected_audience:
        raise PermissionError("invalid audience")

    return payload


def current_tenant(token):
    claims = verify_jwt(token, "duopoly-api")
    return claims["tenant_id"]

